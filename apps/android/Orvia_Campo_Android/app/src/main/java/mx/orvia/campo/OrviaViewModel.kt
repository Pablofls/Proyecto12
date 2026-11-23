package mx.orvia.campo

import android.app.Application
import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import mx.orvia.campo.data.*
import mx.orvia.campo.network.ApiError
import mx.orvia.campo.network.OrviaApi
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

/** Datos visibles proceden del servidor o de la cola real; no hay mocks. */
class OrviaViewModel(application: Application) : AndroidViewModel(application) {
    private val store = SecureStore(application)
    private val api = OrviaApi()
    var host by mutableStateOf(store.getHost()); private set
    var session by mutableStateOf(store.loadSession()); private set
    var currentTab by mutableStateOf("inicio")
    var busy by mutableStateOf(false); private set
    var syncing by mutableStateOf(false); private set
    var notice by mutableStateOf(""); private set
    var error by mutableStateOf(""); private set
    var sales by mutableStateOf<List<Sale>>(emptyList()); private set
    var saleLines by mutableStateOf<List<SaleLine>>(emptyList()); private set
    var returns by mutableStateOf<List<ReturnItem>>(emptyList()); private set
    var monitorAlerts by mutableStateOf<List<JSONObject>>(emptyList()); private set
    var reasons by mutableStateOf<List<Reason>>(emptyList()); private set
    var pending by mutableStateOf(session?.let { store.loadQueueFor(it.id) }.orEmpty()); private set
    var selectedSale by mutableStateOf<Sale?>(null); private set
    var chosenPhoto by mutableStateOf<PhotoData?>(null); private set
    var photoLoading by mutableStateOf(false); private set
    var location by mutableStateOf<Pair<Double, Double>?>(null); private set
    var scannerText by mutableStateOf(""); private set

    private fun job(block: suspend () -> Unit) {
        viewModelScope.launch {
            busy = true; error = ""; notice = ""
            try { block() } catch (e: Exception) { error = e.message ?: "Error inesperado" }
            finally { busy = false }
        }
    }
    private suspend fun call(path: String, method: String = "GET",
                             json: JSONObject? = null, auth: Boolean = true): JSONObject = withContext(Dispatchers.IO) {
        val before = session
        try { api.call(host, path, method, if (auth) before?.accessToken else null, json) }
        catch (e: ApiError) {
            if (e.status != 401 || !auth || before == null || before.refreshToken.isBlank()) throw e
            val renewed = api.call(host, "/api/v1/auth/refresh", "POST", null,
                JSONObject().put("refresh_token", before.refreshToken))
            val after = before.copy(accessToken = renewed.getString("access_token"))
            withContext(Dispatchers.Main) { session = after; store.saveSession(after) }
            api.call(host, path, method, after.accessToken, json)
        }
    }
    fun saveHost(raw: String) {
        if (session != null) { error = "Cierra sesion antes de cambiar el servidor."; return }
        val cleaned = raw.trim().trimEnd('/')
        if (!api.hostValid(cleaned)) { error = "Indica http(s)://IP-o-dominio, sin puerto ni ruta."; return }
        store.setHost(cleaned); host = cleaned; notice = "Servidor guardado"; error = ""
    }
    fun login(email: String, password: String) = job {
        require(api.hostValid(host)) { "Configura primero la IP del servidor." }
        val result = call("/api/v1/auth/login", "POST",
            JSONObject().put("email", email.trim().lowercase(Locale.ROOT)).put("password", password), false)
        val person = result.getJSONObject("usuario")
        val s = Session(person.getInt("id"), person.optString("nombre"), person.optString("email"),
            person.getString("rol"), result.getString("access_token"), result.getString("refresh_token"))
        store.saveSession(s); session = s
        pending = store.loadQueueFor(s.id)
        notice = "Sesion iniciada correctamente"
        currentTab = "inicio"
        refreshDataInternal()
    }
    fun logout() = job {
        try { call("/api/v1/auth/logout", "POST") }
        catch (_: Exception) { /* Caducada/revocada: se cierra localmente de todas formas. */ }
        store.remove("session")
        session = null; sales = emptyList(); returns = emptyList(); reasons = emptyList(); monitorAlerts = emptyList()
        saleLines = emptyList(); selectedSale = null; chosenPhoto = null; pending = emptyList()
        currentTab = "inicio"; notice = "Sesion cerrada"
    }
    fun refreshData() = job { refreshDataInternal(); notice = "Datos actualizados" }
    private suspend fun refreshDataInternal() {
        val role = session?.role ?: return
        if (role == Roles.CLIENTE) {
            val v = call("/api/v1/ventas?por_pagina=50")
            sales = v.list("datos").map { Sale(it.optInt("id"), it.optString("folio_venta"),
                it.optString("fecha_venta"), it.optString("total")) }
            val m = call("/api/v1/catalogos/motivos?por_pagina=100")
            reasons = m.list("datos").map { Reason(it.optInt("id"), it.optString("nombre")) }
        }
        try {
            val r = call("/api/v1/devoluciones?por_pagina=50")
            returns = r.list("datos").map { ReturnItem(it.optInt("id"), it.optString("folio_devolucion"),
                it.optString("producto"), it.optString("estado"), it.optString("fecha_solicitud"),
                it.optString("numero_lote")) }
        } catch (e: ApiError) {
            if (role == Roles.CLIENTE) throw e
            // Algunos roles de campo no pueden listar expedientes globales.
            returns = emptyList()
        }
        if (role in listOf(Roles.SUPERVISOR, Roles.ADMIN)) {
            try {
                monitorAlerts = call("/api/v1/monitoreo/alertas?estado=activa&por_pagina=25").list("datos")
            } catch (_: Exception) { monitorAlerts = emptyList() }
        }
    }
    fun chooseSale(sale: Sale) = job {
        selectedSale = sale
        val detail = call("/api/v1/ventas/${sale.id}")
        saleLines = detail.list("lineas").map { SaleLine(it.optInt("id"), it.optString("producto"),
            it.optString("numero_lote"), it.optInt("disponible"), it.optInt("cantidad")) }
        currentTab = "nueva"
    }
    fun submitReturn(lineId: Int, motiveId: Int, description: String, count: Int) = job {
        require(session?.role == Roles.CLIENTE) { "Solo clientes pueden usar esta pantalla" }
        require(lineId > 0 && motiveId > 0 && count > 0) { "Selecciona producto, motivo y cantidad valida" }
        require(description.trim().length in 10..2000) { "La descripcion requiere entre 10 y 2000 caracteres" }
        val eligibility = call("/api/v1/devoluciones/elegibilidad?venta_detalle_id=$lineId")
        require(eligibility.optBoolean("elegible") && count <= eligibility.optInt("disponible")) {
            "El producto no es elegible o la cantidad supera lo disponible."
        }
        val created = call("/api/v1/devoluciones", "POST", JSONObject()
            .put("venta_detalle_id", lineId).put("motivo_id", motiveId)
            .put("descripcion_problema", description.trim()).put("cantidad_devuelta", count))
        val newId = created.getInt("id")
        // El servidor ya creo la devolucion: nunca reintentar el alta si falla la foto.
        val photo = chosenPhoto
        chosenPhoto = null
        var extra = ""
        if (photo != null) {
            try { withContext(Dispatchers.IO) {
                api.uploadPhoto(host, session?.accessToken ?: error("Sesion terminada"), newId, photo)
            } } catch (e: Exception) { extra = " Foto no subida: ${e.message}. Adjuntala desde Evidencias." }
        }
        notice = "Devolucion ${created.optString("folio_devolucion")} registrada.$extra"
        selectedSale = null; saleLines = emptyList(); currentTab = "devoluciones"
        try { refreshDataInternal() } catch (_: Exception) { /* Alta confirmada, refresco no. */ }
    }
    fun selectPhoto(uri: Uri) {
        viewModelScope.launch {
            photoLoading = true; error = ""; chosenPhoto = null
            try { chosenPhoto = withContext(Dispatchers.IO) { PhotoProcessor.prepare(getApplication(), uri) }
                notice = "Fotografia lista: ${(chosenPhoto?.bytes?.size ?: 0) / 1024} KB"
            } catch (e: Exception) { error = e.message ?: "No se pudo preparar la foto" }
            finally { photoLoading = false }
        }
    }
    fun clearPhoto() { chosenPhoto = null }
    fun setLocation(latitude: Double, longitude: Double) { location = latitude to longitude }
    fun scanResult(value: String) { scannerText = value; notice = "Codigo escaneado: $value" }
    fun clearScan() { scannerText = "" }

    /** Guarda antes de enviar. Nunca marca confirmada una operacion que no acepto el servidor. */
    private fun enqueue(type: String, data: JSONObject) {
        val s = session ?: error("Inicia sesion")
        val next = pending + PendingOperation.create(type, data)
        store.saveQueueFor(s.id, next)
        pending = next
        notice = "Guardado en este dispositivo. Pendiente de confirmacion del servidor."
        error = ""; currentTab = "cola"
    }
    fun queueStage(idText: String, expected: String, next: String) {
        val id = idText.trim().toIntOrNull() ?: 0
        if (id < 1) { error = "Indica un ID numerico valido de recoleccion"; return }
        if (session?.role !in listOf(Roles.RECOLECTOR, Roles.COORDINADOR)) {
            error = "Tu rol no puede registrar movimiento de campo"; return
        }
        if ((expected == "asignada" && next !in listOf("en_transito", "fallida")) ||
            (expected == "en_transito" && next !in listOf("completada", "fallida")) ||
            expected !in listOf("asignada", "en_transito")) {
            error = "Selecciona una transicion permitida"; return
        }
        val data = JSONObject().put("recoleccion_id", id).put("estado_esperado", expected).put("estado", next)
        location?.let { data.put("ubicacion", JSONObject().put("latitud", it.first).put("longitud", it.second)) }
        enqueue("estado_recoleccion", data)
        location = null
    }
    fun queueReception(returnIdText: String, matches: Boolean) {
        val id = returnIdText.trim().toIntOrNull() ?: 0
        if (id < 1) { error = "Indica un ID de devolucion valido"; return }
        if (session?.role !in listOf(Roles.OPERADOR, Roles.CENTRO)) {
            error = "Tu rol no puede confirmar recepciones"; return
        }
        enqueue("recepcion", JSONObject().put("devolucion_id", id).put("coincide_expediente", matches))
    }
    fun queueEvidence(returnIdText: String, comment: String) {
        val id = returnIdText.trim().toIntOrNull() ?: 0
        if (id < 1) { error = "Indica un ID de devolucion valido"; return }
        if (session?.role !in listOf(Roles.RECOLECTOR, Roles.OPERADOR, Roles.CENTRO)) {
            error = "Tu rol no puede adjuntar evidencias offline"; return
        }
        if (comment.isBlank() && chosenPhoto == null) { error = "Escribe comentario o adjunta foto"; return }
        if (comment.length > 2000) { error = "Comentario demasiado largo"; return }
        val data = JSONObject().put("devolucion_id", id).put("comentario", comment.trim())
        chosenPhoto?.let { p ->
            data.put("archivo", JSONObject().put("nombre", p.name)
                .put("contenido_base64", android.util.Base64.encodeToString(p.bytes, android.util.Base64.NO_WRAP))
                .put("sha256", p.sha256))
        }
        enqueue("evidencia", data)
        chosenPhoto = null
    }
    fun deleteQueued(id: String) {
        val s = session ?: return
        val next = pending.filterNot { it.id == id }
        store.saveQueueFor(s.id, next); pending = next
    }
    fun syncQueue() {
        if (syncing || session == null || pending.none { it.status in listOf("pendiente", "reintentar") }) return
        viewModelScope.launch {
            syncing = true; error = ""; notice = ""
            try {
                val s = session ?: return@launch
                val device = "android-orvia-${s.id}"
                var accepted = 0
                for (item in pending.toList()) {
                    if (item.status !in listOf("pendiente", "reintentar")) continue
                    val result = try {
                        val body = JSONObject().put("dispositivo_id", device)
                            .put("operaciones", JSONArray().put(item.wireJson()))
                        call("/api/v1/sincronizacion/operaciones", "POST", body)
                    } catch (e: Exception) {
                        // Red caida: conservar el MISMO UUID y el payload para reintentar.
                        error = "Sin conexion o servidor no disponible: ${e.message}"
                        break
                    }
                    val answer = result.list("resultados").firstOrNull()
                    val status = answer?.optString("estado") ?: "reintentar"
                    val detail = answer?.optJSONObject("motivo")?.optString("mensaje").orEmpty()
                    val newPending = if (status == "aceptada") {
                        accepted++
                        pending.filterNot { it.id == item.id }
                    } else {
                        pending.map { if (it.id == item.id) it.copy(status = status, detail = detail) else it }
                    }
                    // Guardar el resultado antes de procesar el siguiente elemento.
                    store.saveQueueFor(s.id, newPending); pending = newPending
                    if (status == "reintentar") break
                }
                notice = "$accepted operacion(es) confirmadas por el servidor."
            } catch (e: Exception) { error = e.message ?: "Fallo al sincronizar" }
            finally { syncing = false }
        }
    }
    fun uploadPhotoToReturn(returnIdText: String) = job {
        require(session?.role == Roles.CLIENTE) { "Esta accion requiere rol Cliente" }
        val id = returnIdText.trim().toIntOrNull() ?: 0
        require(id > 0) { "ID de devolucion no valido" }
        val photo = chosenPhoto ?: error("Selecciona una fotografia")
        withContext(Dispatchers.IO) { api.uploadPhoto(host, session!!.accessToken, id, photo) }
        chosenPhoto = null; notice = "Fotografia adjuntada al expediente #$id"
    }
}
