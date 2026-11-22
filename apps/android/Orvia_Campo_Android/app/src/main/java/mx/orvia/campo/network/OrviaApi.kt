package mx.orvia.campo.network

import mx.orvia.campo.data.PhotoData
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.net.URI
import java.util.concurrent.TimeUnit

class ApiError(val status: Int, override val message: String) : Exception(message)

/** Cliente del punto de entrada unico de Orvia (reverse proxy). */
class OrviaApi {
    private val client = OkHttpClient.Builder()
        .connectTimeout(12, TimeUnit.SECONDS)
        .readTimeout(35, TimeUnit.SECONDS)
        .writeTimeout(35, TimeUnit.SECONDS)
        .build()

    fun hostValid(host: String): Boolean = try {
        val uri = URI(host)
        (uri.scheme == "http" || uri.scheme == "https") &&
            !uri.host.isNullOrBlank() && uri.port == -1 &&
            (uri.path.isNullOrEmpty() || uri.path == "/") &&
            uri.query == null && uri.userInfo == null && uri.fragment == null
    } catch (_: Exception) { false }

    fun url(host: String, path: String): String {
        require(hostValid(host)) { "Usa http(s)://IP-o-dominio sin puerto. Ej: http://10.0.2.2" }
        require(path.startsWith("/") && !path.startsWith("//")) { "Ruta no valida" }
        return "${host.trimEnd('/')}$path"
    }

    fun call(host: String, path: String, method: String = "GET",
             token: String? = null, payload: JSONObject? = null): JSONObject {
        val body = if (method == "GET" || method == "DELETE") null
            else (payload ?: JSONObject()).toString().toRequestBody("application/json; charset=utf-8".toMediaType())
        val request = Request.Builder().url(url(host, path))
            .header("Accept", "application/json")
            .header("X-Correlation-ID", java.util.UUID.randomUUID().toString())
            .apply { if (!token.isNullOrEmpty()) header("Authorization", "Bearer $token") }
            .method(method, body).build()
        return execute(request)
    }

    fun uploadPhoto(host: String, token: String, returnId: Int, photo: PhotoData): JSONObject {
        val body = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart("devolucion_id", returnId.toString())
            .addFormDataPart("etapa", "solicitud")
            .addFormDataPart("comentario", "Evidencia fotografica de la solicitud")
            .addFormDataPart("archivo", photo.name,
                photo.bytes.toRequestBody("image/jpeg".toMediaType()))
            .build()
        val request = Request.Builder().url(url(host, "/api/v1/evidencias"))
            .header("Accept", "application/json")
            .header("Authorization", "Bearer $token")
            .post(body).build()
        return execute(request)
    }

    private fun execute(request: Request): JSONObject = client.newCall(request).execute().use { response ->
        val raw = response.body?.string().orEmpty()
        val result = try { JSONObject(raw) } catch (_: Exception) { JSONObject() }
        if (!response.isSuccessful) {
            val error = result.optJSONObject("error")
            throw ApiError(response.code,
                error?.optString("mensaje")?.takeIf { it.isNotBlank() }
                    ?: "HTTP ${response.code}: ${request.url.encodedPath}")
        }
        return result
    }
}
