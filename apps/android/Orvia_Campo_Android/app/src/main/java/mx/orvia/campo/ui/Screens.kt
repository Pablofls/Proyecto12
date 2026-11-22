package mx.orvia.campo.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.automirrored.outlined.AssignmentReturn
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.automirrored.outlined.ReceiptLong
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import mx.orvia.campo.R
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import mx.orvia.campo.OrviaViewModel
import mx.orvia.campo.data.*

private val cardShape = RoundedCornerShape(24.dp)
private val gradient = Brush.linearGradient(listOf(Color(0xFF123A32), Color(0xFF04785D), Forest))

private data class Nav(val key: String, val title: String, val icon: ImageVector)

@Composable
fun OrviaRoot(model: OrviaViewModel, onCamera: () -> Unit, onGallery: () -> Unit,
              onScan: () -> Unit, onLocation: () -> Unit) {
    val person = model.session
    if (person == null) {
        LoginView(model)
        return
    }
    val tabs = when (person.role) {
        Roles.CLIENTE -> listOf(Nav("inicio", "Inicio", Icons.Outlined.Home),
            Nav("devoluciones", "Solicitudes", Icons.AutoMirrored.Outlined.AssignmentReturn),
            Nav("nueva", "Nueva", Icons.Outlined.AddCircleOutline),
            Nav("perfil", "Perfil", Icons.Outlined.PersonOutline))
        Roles.RECOLECTOR, Roles.COORDINADOR, Roles.OPERADOR, Roles.CENTRO -> listOf(
            Nav("inicio", "Inicio", Icons.Outlined.Home),
            Nav("campo", "Campo", Icons.Outlined.LocalShipping),
            Nav("cola", "Pendientes", Icons.Outlined.CloudUpload),
            Nav("perfil", "Perfil", Icons.Outlined.PersonOutline))
        Roles.SUPERVISOR, Roles.ADMIN -> listOf(
            Nav("inicio", "Inicio", Icons.Outlined.Home),
            Nav("devoluciones", "Expedientes", Icons.AutoMirrored.Outlined.AssignmentReturn),
            Nav("alertas", "Alertas", Icons.Outlined.NotificationsActive),
            Nav("perfil", "Perfil", Icons.Outlined.PersonOutline))
        else -> listOf(Nav("inicio", "Inicio", Icons.Outlined.Home),
            Nav("devoluciones", "Expedientes", Icons.AutoMirrored.Outlined.AssignmentReturn),
            Nav("cola", "Pendientes", Icons.Outlined.CloudUpload),
            Nav("perfil", "Perfil", Icons.Outlined.PersonOutline))
    }
    Scaffold(
        containerColor = Canvas,
        topBar = {
            Row(Modifier.fillMaxWidth().background(Color.White)
                .padding(horizontal = 20.dp, vertical = 15.dp),
                verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Image(
                        painter = painterResource(R.drawable.orvia_logo),
                        contentDescription = "Orvia, logo oficial",
                        modifier = Modifier.width(124.dp).height(43.dp),
                        contentScale = ContentScale.Fit
                    )
                    Text("CAMPO / OPERACIONES", fontSize = 10.sp, color = Muted,
                        fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                }
                IconButton(onClick = { model.refreshData() }, enabled = !model.busy) {
                    Icon(Icons.Outlined.Refresh, contentDescription = "Actualizar", tint = Dark)
                }
            }
        },
        bottomBar = {
            NavigationBar(containerColor = Color.White, tonalElevation = 0.dp) {
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = model.currentTab == tab.key,
                        onClick = { model.currentTab = tab.key },
                        icon = { Icon(tab.icon, contentDescription = null) },
                        label = { Text(tab.title, maxLines = 1, fontSize = 10.sp) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = Forest, selectedTextColor = Forest,
                            indicatorColor = EmeraldSoft, unselectedIconColor = Muted)
                    )
                }
            }
        }
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState())
            .padding(horizontal = 19.dp, vertical = 20.dp)) {
            if (model.busy || model.photoLoading || model.syncing) {
                LinearProgressIndicator(Modifier.fillMaxWidth(), color = Forest)
                Spacer(Modifier.height(12.dp))
            }
            Feedback(model.error, model.notice)
            when (model.currentTab) {
                "inicio" -> HomeView(model)
                "devoluciones" -> ReturnsView(model, onCamera, onGallery)
                "nueva" -> NewReturnView(model, onCamera, onGallery)
                "campo" -> FieldView(model, onCamera, onGallery, onScan, onLocation)
                "cola" -> QueueView(model)
                "alertas" -> AlertsView(model)
                "perfil" -> ProfileView(model)
                else -> HomeView(model)
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable private fun Feedback(error: String, notice: String) {
    if (error.isNotBlank()) {
        Surface(color = Color(0xFFFFEEEE), shape = RoundedCornerShape(14.dp)) {
            Row(Modifier.fillMaxWidth().padding(13.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.ErrorOutline, contentDescription = null, tint = Color(0xFFB33B3B))
                Spacer(Modifier.width(10.dp))
                Text(error, style = MaterialTheme.typography.bodySmall, color = Color(0xFF8E2828))
            }
        }
        Spacer(Modifier.height(14.dp))
    }
    if (notice.isNotBlank()) {
        Surface(color = EmeraldSoft, shape = RoundedCornerShape(14.dp)) {
            Row(Modifier.fillMaxWidth().padding(13.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.CheckCircleOutline, contentDescription = null, tint = Forest)
                Spacer(Modifier.width(10.dp))
                Text(notice, style = MaterialTheme.typography.bodySmall, color = Dark)
            }
        }
        Spacer(Modifier.height(14.dp))
    }
}

@Composable private fun LoginView(vm: OrviaViewModel) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var server by remember { mutableStateOf(vm.host) }
    Column(Modifier.fillMaxSize().background(Canvas).verticalScroll(rememberScrollState())
        .padding(28.dp), verticalArrangement = Arrangement.Center) {
        Spacer(Modifier.height(46.dp))
        Image(
            painter = painterResource(R.drawable.orvia_logo),
            contentDescription = "Orvia, logo oficial",
            modifier = Modifier.width(184.dp).height(70.dp),
            contentScale = ContentScale.Fit
        )
        Spacer(Modifier.height(20.dp))
        Text("Orvia Campo", fontWeight = FontWeight.ExtraBold, fontSize = 35.sp, color = Dark)
        Spacer(Modifier.height(4.dp))
        Text("Tu operación, donde suceden las cosas.", style = MaterialTheme.typography.bodyLarge,
            color = Muted)
        Spacer(Modifier.height(30.dp))
        Feedback(vm.error, vm.notice)
        OrviaCard {
            Text("Accede a tu espacio", fontWeight = FontWeight.Bold, fontSize = 20.sp)
            Spacer(Modifier.height(17.dp))
            OutlinedTextField(value = email, onValueChange = { email = it },
                modifier = Modifier.fillMaxWidth(), label = { Text("Correo corporativo") },
                leadingIcon = { Icon(Icons.Outlined.AlternateEmail, contentDescription = null) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email), singleLine = true)
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(value = password, onValueChange = { password = it },
                modifier = Modifier.fillMaxWidth(), label = { Text("Contraseña") },
                leadingIcon = { Icon(Icons.Outlined.Lock, contentDescription = null) },
                visualTransformation = PasswordVisualTransformation(), singleLine = true)
            Spacer(Modifier.height(20.dp))
            Button(onClick = { vm.login(email, password) }, modifier = Modifier.fillMaxWidth().height(52.dp),
                enabled = !vm.busy && email.isNotBlank() && password.isNotBlank(),
                shape = RoundedCornerShape(16.dp)) {
                Text("Entrar a Orvia", fontWeight = FontWeight.Bold)
                Spacer(Modifier.width(7.dp))
                Icon(Icons.AutoMirrored.Outlined.ArrowForward, contentDescription = null)
            }
        }
        Spacer(Modifier.height(18.dp))
        OrviaCard {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Dns, contentDescription = null, tint = Forest)
                Spacer(Modifier.width(8.dp))
                Text("Conexión con tu VM", fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(9.dp))
            OutlinedTextField(value = server, onValueChange = { server = it },
                modifier = Modifier.fillMaxWidth(), label = { Text("Servidor Orvia") },
                placeholder = { Text("http://10.0.2.2") }, singleLine = true)
            Spacer(Modifier.height(7.dp))
            Text("Emulador: 10.0.2.2 · Dispositivo: IP privada accesible de tu VM. Sin puerto.",
                fontSize = 11.sp, color = Muted)
            Spacer(Modifier.height(12.dp))
            OutlinedButton(onClick = { vm.saveHost(server) }, modifier = Modifier.fillMaxWidth()) {
                Text("Guardar servidor")
            }
        }
        Spacer(Modifier.height(20.dp))
        Text("JWT protegido · Datos reales · Sin cuentas de demostración inventadas",
            color = Muted, fontSize = 11.sp)
    }
}

@Composable private fun OrviaCard(content: @Composable ColumnScope.() -> Unit) {
    Surface(shape = cardShape, color = Color.White, shadowElevation = 1.dp,
        modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(20.dp), content = content)
    }
}

@Composable private fun Title(kicker: String, headline: String, subtitle: String? = null) {
    Text(kicker.uppercase(), color = Forest, fontWeight = FontWeight.Bold,
        fontSize = 11.sp, letterSpacing = 1.5.sp)
    Spacer(Modifier.height(5.dp))
    Text(headline, color = Dark, fontWeight = FontWeight.ExtraBold, fontSize = 27.sp,
        lineHeight = 30.sp)
    if (!subtitle.isNullOrBlank()) {
        Spacer(Modifier.height(7.dp))
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = Muted)
    }
    Spacer(Modifier.height(20.dp))
}

@Composable private fun HomeView(vm: OrviaViewModel) {
    val session = vm.session ?: return
    val shortName = session.name.substringBefore(' ').ifBlank { "Equipo" }
    Title("OPERACIÓN CONECTADA", "Hola, $shortName", "${session.role} · Tu espacio de trabajo")
    Box(Modifier.fillMaxWidth().clip(cardShape).background(gradient).padding(24.dp)) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.VerifiedUser, contentDescription = null, tint = Color(0xFFADFFE0))
                Spacer(Modifier.width(9.dp))
                Text("IDENTIDAD VERIFICADA", color = Color(0xFFCBF7E9),
                    fontWeight = FontWeight.Bold, fontSize = 11.sp, letterSpacing = 1.1.sp)
            }
            Spacer(Modifier.height(19.dp))
            Text("Cada movimiento cuenta.", color = Color.White,
                fontWeight = FontWeight.ExtraBold, fontSize = 25.sp, lineHeight = 29.sp)
            Spacer(Modifier.height(7.dp))
            Text("Registra operaciones reales. Orvia conserva su trazabilidad.",
                color = Color(0xFFE0F6ED), fontSize = 13.sp)
            Spacer(Modifier.height(17.dp))
            Surface(color = Color.White.copy(alpha = 0.14f), shape = RoundedCornerShape(30.dp)) {
                Text("${vm.host}  •  sesión activa", color = Color.White,
                    modifier = Modifier.padding(horizontal = 13.dp, vertical = 7.dp), fontSize = 11.sp)
            }
        }
    }
    Spacer(Modifier.height(18.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        SummaryMetric("Expedientes", vm.returns.size.toString(), Icons.AutoMirrored.Outlined.AssignmentReturn,
            Modifier.weight(1f))
        SummaryMetric("Pendientes", vm.pending.count { it.status in listOf("pendiente", "reintentar") }.toString(),
            Icons.Outlined.CloudUpload, Modifier.weight(1f))
    }
    Spacer(Modifier.height(22.dp))
    Text("Acceso según tu rol", fontWeight = FontWeight.ExtraBold, fontSize = 19.sp, color = Dark)
    Spacer(Modifier.height(12.dp))
    when (session.role) {
        Roles.CLIENTE -> {
            ActionTile(Icons.Outlined.ShoppingBag, "Mis compras", "Selecciona una venta para solicitar devolución") {
                vm.currentTab = "nueva"
            }
            Spacer(Modifier.height(11.dp))
            ActionTile(Icons.AutoMirrored.Outlined.AssignmentReturn, "Mis solicitudes", "Consulta tus expedientes y sus estados") {
                vm.currentTab = "devoluciones"
            }
        }
        Roles.RECOLECTOR, Roles.COORDINADOR -> {
            ActionTile(Icons.Outlined.LocalShipping, "Trabajo en campo", "Escanea un ID, captura GPS y avanza el estado") {
                vm.currentTab = "campo"
            }
            Spacer(Modifier.height(11.dp))
            ActionTile(Icons.Outlined.CameraAlt, "Evidencia offline", "Fotografías e incidencias con integridad SHA-256") {
                vm.currentTab = "campo"
            }
        }
        Roles.OPERADOR, Roles.CENTRO -> {
            ActionTile(Icons.Outlined.Inventory2, "Recepción de productos", "Compara lo recibido con el expediente autorizado") {
                vm.currentTab = "campo"
            }
        }
        else -> {
            ActionTile(Icons.AutoMirrored.Outlined.AssignmentReturn, "Expedientes", "Consulta el alcance permitido a tu rol") {
                vm.currentTab = "devoluciones"
            }
            if (session.role in listOf(Roles.SUPERVISOR, Roles.ADMIN)) {
                Spacer(Modifier.height(11.dp))
                ActionTile(Icons.Outlined.NotificationsActive, "Alertas operativas",
                    "Consulta los incidentes del monitoreo en tiempo real") {
                    vm.currentTab = "alertas"
                }
            }
        }
    }
    Spacer(Modifier.height(20.dp))
    if (vm.returns.isNotEmpty()) {
        Text("Actividad reciente", fontWeight = FontWeight.ExtraBold, fontSize = 19.sp)
        Spacer(Modifier.height(10.dp))
        vm.returns.take(3).forEach { ReturnCard(it); Spacer(Modifier.height(9.dp)) }
    } else {
        Text("No hay expedientes accesibles para mostrar con esta cuenta.",
            fontSize = 12.sp, color = Muted)
    }
}

@Composable private fun SummaryMetric(title: String, value: String, icon: ImageVector, modifier: Modifier) {
    Surface(modifier = modifier, shape = RoundedCornerShape(20.dp), color = Color.White) {
        Column(Modifier.padding(17.dp)) {
            Icon(icon, contentDescription = null, tint = Forest)
            Spacer(Modifier.height(12.dp))
            Text(value, fontWeight = FontWeight.ExtraBold, fontSize = 29.sp, color = Dark)
            Text(title, color = Muted, fontSize = 12.sp)
        }
    }
}

@Composable private fun ActionTile(icon: ImageVector, title: String, subtitle: String, onClick: () -> Unit) {
    Surface(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick), color = Color.White,
        shape = RoundedCornerShape(18.dp)) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(45.dp).clip(RoundedCornerShape(14.dp)).background(EmeraldSoft),
                contentAlignment = Alignment.Center) {
                Icon(icon, contentDescription = null, tint = Forest)
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, color = Dark)
                Text(subtitle, color = Muted, fontSize = 11.sp, lineHeight = 16.sp)
            }
            Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = Muted)
        }
    }
}

@Composable private fun ReturnCard(item: ReturnItem, onClick: (() -> Unit)? = null) {
    Surface(modifier = Modifier.fillMaxWidth().then(if (onClick != null) Modifier.clickable(onClick = onClick)
        else Modifier), shape = RoundedCornerShape(18.dp), color = Color.White) {
        Row(Modifier.padding(17.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(42.dp).clip(RoundedCornerShape(13.dp)).background(EmeraldSoft),
                contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.Inventory2, contentDescription = null, tint = Forest)
            }
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text(item.folio, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp)
                Text(item.product, fontSize = 12.sp, color = Muted, maxLines = 1,
                    overflow = TextOverflow.Ellipsis)
                Text("Lote ${item.lot}", fontSize = 10.sp, color = Muted)
            }
            Column(horizontalAlignment = Alignment.End) {
                Surface(color = EmeraldSoft, shape = RoundedCornerShape(40.dp)) {
                    Text(item.status.replace('_', ' '), fontSize = 10.sp, color = Forest,
                        modifier = Modifier.padding(horizontal = 9.dp, vertical = 6.dp))
                }
                Text("#${item.id}", fontSize = 10.sp, color = Muted)
            }
        }
    }
}

@Composable private fun ReturnsView(vm: OrviaViewModel, onCamera: () -> Unit, onGallery: () -> Unit) {
    Title("TRAZABILIDAD", "Devoluciones", "Información obtenida directamente de Orvia-Oficial.")
    if (vm.returns.isEmpty()) {
        OrviaCard {
            Text("No hay solicitudes visibles", fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(5.dp))
            Text("Actualiza o consulta con un rol que tenga permiso para ver expedientes.", color = Muted,
                fontSize = 12.sp)
            Spacer(Modifier.height(12.dp))
            OutlinedButton(onClick = vm::refreshData) { Text("Actualizar solicitudes") }
        }
    } else {
        vm.returns.forEach { item -> ReturnCard(item); Spacer(Modifier.height(10.dp)) }
    }
    if (vm.session?.role == Roles.CLIENTE) {
        Spacer(Modifier.height(22.dp))
        var returnId by remember { mutableStateOf("") }
        Text("Adjuntar fotografía", fontWeight = FontWeight.ExtraBold, fontSize = 19.sp)
        Spacer(Modifier.height(11.dp))
        OrviaCard {
            Text("Solo para solicitudes propias en revisión o solicitadas.", color = Muted, fontSize = 12.sp)
            Spacer(Modifier.height(10.dp))
            OutlinedTextField(value = returnId, onValueChange = { returnId = it.filter(Char::isDigit) },
                modifier = Modifier.fillMaxWidth(), label = { Text("ID numérico de devolución") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            Spacer(Modifier.height(11.dp))
            PhotoControls(vm, onCamera, onGallery)
            Spacer(Modifier.height(12.dp))
            Button(onClick = { vm.uploadPhotoToReturn(returnId) },
                enabled = !vm.busy && vm.chosenPhoto != null,
                modifier = Modifier.fillMaxWidth()) { Text("Subir fotografía al expediente") }
        }
    }
}

@Composable private fun NewReturnView(vm: OrviaViewModel, onCamera: () -> Unit, onGallery: () -> Unit) {
    if (vm.session?.role != Roles.CLIENTE) {
        Title("PERMISOS", "Sin acceso", "Solo el cliente puede solicitar una devolución aquí.")
        return
    }
    Title("NUEVA SOLICITUD", "Solicitar devolución", "Elegimos una venta real; Orvia valida el plazo y la cantidad.")
    if (vm.sales.isEmpty()) {
        OrviaCard {
            Text("No hay ventas disponibles", fontWeight = FontWeight.Bold)
            Text("La app no inventa productos ni ventas. Verifica que el usuario tenga compras.",
                color = Muted, fontSize = 12.sp)
        }
        return
    }
    Text("01 / Selecciona tu compra", fontWeight = FontWeight.Bold, fontSize = 15.sp)
    Spacer(Modifier.height(12.dp))
    vm.sales.take(25).forEach { sale ->
        Surface(modifier = Modifier.fillMaxWidth().clickable { vm.chooseSale(sale) },
            color = if (vm.selectedSale?.id == sale.id) EmeraldSoft else Color.White,
            shape = RoundedCornerShape(16.dp)) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.AutoMirrored.Outlined.ReceiptLong, contentDescription = null, tint = Forest)
                Spacer(Modifier.width(11.dp))
                Column(Modifier.weight(1f)) {
                    Text(sale.folio, fontWeight = FontWeight.Bold)
                    Text("${sale.date} · $${sale.total}", color = Muted, fontSize = 11.sp)
                }
                Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = Forest)
            }
        }
        Spacer(Modifier.height(8.dp))
    }
    if (vm.selectedSale != null) {
        Spacer(Modifier.height(14.dp))
        Text("02 / Producto y motivo", fontWeight = FontWeight.Bold, fontSize = 15.sp)
        Spacer(Modifier.height(11.dp))
        var lineId by remember(vm.selectedSale?.id) { mutableIntStateOf(0) }
        var reasonId by remember { mutableIntStateOf(0) }
        var quantity by remember { mutableStateOf("1") }
        var description by remember { mutableStateOf("") }
        OrviaCard {
            vm.saleLines.forEach { item ->
                Surface(modifier = Modifier.fillMaxWidth().clickable { lineId = item.id },
                    color = if (lineId == item.id) EmeraldSoft else Canvas,
                    shape = RoundedCornerShape(12.dp)) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(if (lineId == item.id) Icons.Outlined.RadioButtonChecked else
                            Icons.Outlined.RadioButtonUnchecked, contentDescription = null, tint = Forest)
                        Spacer(Modifier.width(8.dp))
                        Column {
                            Text(item.product, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                            Text("Lote ${item.lot} · Disponible: ${item.available}", color = Muted, fontSize = 11.sp)
                        }
                    }
                }
                Spacer(Modifier.height(8.dp))
            }
            Spacer(Modifier.height(8.dp))
            Text("Motivo de devolución", fontWeight = FontWeight.Medium, fontSize = 13.sp)
            Spacer(Modifier.height(7.dp))
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                vm.reasons.forEach { reason ->
                    FilterChip(selected = reasonId == reason.id, onClick = { reasonId = reason.id },
                        label = { Text(reason.name) }, leadingIcon = if (reasonId == reason.id) {
                            { Icon(Icons.Outlined.Check, contentDescription = null, Modifier.size(16.dp)) }
                        } else null)
                }
            }
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(value = quantity, onValueChange = { quantity = it.filter(Char::isDigit) },
                modifier = Modifier.fillMaxWidth(), label = { Text("Cantidad") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), singleLine = true)
            Spacer(Modifier.height(10.dp))
            OutlinedTextField(value = description, onValueChange = { description = it },
                modifier = Modifier.fillMaxWidth(), minLines = 3, maxLines = 5,
                label = { Text("¿Qué ocurrió con el producto?") },
                supportingText = { Text("Mínimo 10 caracteres") })
            Spacer(Modifier.height(13.dp))
            PhotoControls(vm, onCamera, onGallery)
            Spacer(Modifier.height(15.dp))
            Button(onClick = { vm.submitReturn(lineId, reasonId, description,
                quantity.toIntOrNull() ?: 0) },
                enabled = !vm.busy && lineId > 0 && reasonId > 0 && description.trim().length >= 10,
                modifier = Modifier.fillMaxWidth().height(51.dp), shape = RoundedCornerShape(14.dp)) {
                Text("Crear devolución", fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(7.dp))
            Text("La foto es opcional. Si su carga falla, la solicitud permanece creada.",
                fontSize = 11.sp, color = Muted)
        }
    }
}

@Composable private fun PhotoControls(vm: OrviaViewModel, onCamera: () -> Unit, onGallery: () -> Unit) {
    Text("Fotografía", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
    Spacer(Modifier.height(9.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
        OutlinedButton(onClick = onCamera, modifier = Modifier.weight(1f)) {
            Icon(Icons.Outlined.CameraAlt, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(5.dp)); Text("Cámara")
        }
        OutlinedButton(onClick = onGallery, modifier = Modifier.weight(1f)) {
            Icon(Icons.Outlined.PhotoLibrary, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(5.dp)); Text("Galería")
        }
    }
    vm.chosenPhoto?.let { p ->
        Spacer(Modifier.height(9.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Outlined.CheckCircle, contentDescription = null, tint = Forest)
            Spacer(Modifier.width(7.dp))
            Text("Foto lista · ${p.bytes.size / 1024} KB · SHA-256", fontSize = 11.sp,
                color = Forest, modifier = Modifier.weight(1f))
            TextButton(onClick = vm::clearPhoto) { Text("Quitar") }
        }
    }
}

@Composable private fun FieldView(vm: OrviaViewModel, onCamera: () -> Unit, onGallery: () -> Unit,
                                  onScan: () -> Unit, onLocation: () -> Unit) {
    val role = vm.session?.role
    Title("OPERACIONES DE CAMPO", "Trabajo en movimiento",
        "Los registros sin conexión quedan pendientes hasta su aceptación.")
    when (role) {
        Roles.RECOLECTOR, Roles.COORDINADOR -> StagePanel(vm, onScan, onLocation)
        Roles.OPERADOR, Roles.CENTRO -> ReceptionPanel(vm, onScan)
        else -> OrviaCard {
            Text("Tu rol no puede registrar acciones de campo.", color = Muted)
        }
    }
    if (role in listOf(Roles.RECOLECTOR, Roles.OPERADOR, Roles.CENTRO)) {
        Spacer(Modifier.height(20.dp))
        EvidencePanel(vm, onCamera, onGallery, onScan)
    }
}

@Composable private fun StagePanel(vm: OrviaViewModel, onScan: () -> Unit, onLocation: () -> Unit) {
    var id by remember { mutableStateOf("") }
    var expected by remember { mutableStateOf("asignada") }
    var next by remember { mutableStateOf("en_transito") }
    LaunchedEffect(vm.scannerText) {
        vm.scannerText.toIntOrNull()?.let { id = it.toString() }
    }
    OrviaCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Outlined.LocalShipping, contentDescription = null, tint = Forest)
            Spacer(Modifier.width(8.dp))
            Text("Avance de recolección", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
        }
        Spacer(Modifier.height(14.dp))
        OutlinedTextField(value = id, onValueChange = { id = it.filter(Char::isDigit) },
            label = { Text("ID de recolección") }, modifier = Modifier.fillMaxWidth(),
            trailingIcon = { IconButton(onClick = onScan) {
                Icon(Icons.Outlined.QrCodeScanner, contentDescription = "Escanear ID")
            } }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
        Text("Escanea un QR que contenga el ID numérico o escríbelo. Aún no existe un endpoint de asignaciones para Recolector.",
            fontSize = 11.sp, color = Muted)
        Spacer(Modifier.height(16.dp))
        Text("Estado que viste al capturar", fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("asignada", "en_transito").forEach { label ->
                FilterChip(selected = expected == label, onClick = {
                    expected = label
                    next = if (label == "asignada") "en_transito" else "completada"
                }, label = { Text(label.replace('_', ' '), fontSize = 11.sp) })
            }
        }
        Text("Nuevo estado", fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            (if (expected == "asignada") listOf("en_transito", "fallida")
             else listOf("completada", "fallida")).forEach { label ->
                FilterChip(selected = next == label, onClick = { next = label },
                    label = { Text(label.replace('_', ' '), fontSize = 11.sp) })
            }
        }
        Spacer(Modifier.height(10.dp))
        OutlinedButton(onClick = onLocation, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.Outlined.MyLocation, contentDescription = null, modifier = Modifier.size(17.dp))
            Spacer(Modifier.width(6.dp)); Text(if (vm.location == null) "Capturar GPS" else "Actualizar ubicación")
        }
        vm.location?.let { coords ->
            Text("Ubicación real: %.5f, %.5f".format(coords.first, coords.second),
                fontSize = 11.sp, color = Forest)
        }
        Spacer(Modifier.height(13.dp))
        Button(onClick = { vm.queueStage(id, expected, next) },
            modifier = Modifier.fillMaxWidth().height(49.dp), shape = RoundedCornerShape(14.dp)) {
            Icon(Icons.Outlined.Save, contentDescription = null)
            Spacer(Modifier.width(7.dp)); Text("Guardar operación")
        }
    }
}

@Composable private fun ReceptionPanel(vm: OrviaViewModel, onScan: () -> Unit) {
    var id by remember { mutableStateOf("") }
    var matches by remember { mutableStateOf(true) }
    LaunchedEffect(vm.scannerText) { vm.scannerText.toIntOrNull()?.let { id = it.toString() } }
    OrviaCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Outlined.Inventory2, contentDescription = null, tint = Forest)
            Spacer(Modifier.width(8.dp))
            Text("Recepción en almacén", fontWeight = FontWeight.Bold, fontSize = 17.sp)
        }
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(value = id, onValueChange = { id = it.filter(Char::isDigit) },
            label = { Text("ID de devolución") }, modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            trailingIcon = { IconButton(onClick = onScan) {
                Icon(Icons.Outlined.QrCodeScanner, contentDescription = "Escanear")
            } })
        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(checked = matches, onCheckedChange = { matches = it })
            Text("Coincide con el expediente autorizado", fontSize = 12.sp)
        }
        Text("El servidor valida que la recolección esté completada y que no exista una recepción duplicada.",
            fontSize = 11.sp, color = Muted)
        Spacer(Modifier.height(13.dp))
        Button(onClick = { vm.queueReception(id, matches) }, modifier = Modifier.fillMaxWidth()) {
            Text("Guardar recepción pendiente")
        }
    }
}

@Composable private fun EvidencePanel(vm: OrviaViewModel, onCamera: () -> Unit, onGallery: () -> Unit,
                                     onScan: () -> Unit) {
    var id by remember { mutableStateOf("") }
    var comment by remember { mutableStateOf("") }
    LaunchedEffect(vm.scannerText) { vm.scannerText.toIntOrNull()?.let { id = it.toString() } }
    OrviaCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Outlined.CameraAlt, contentDescription = null, tint = Forest)
            Spacer(Modifier.width(8.dp))
            Text("Evidencia de campo", fontWeight = FontWeight.Bold, fontSize = 17.sp)
        }
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(value = id, onValueChange = { id = it.filter(Char::isDigit) },
            label = { Text("ID de devolución") }, modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            trailingIcon = { IconButton(onClick = onScan) {
                Icon(Icons.Outlined.QrCodeScanner, contentDescription = "Escanear")
            } })
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(value = comment, onValueChange = { comment = it },
            label = { Text("Incidencia / condición del paquete") },
            modifier = Modifier.fillMaxWidth(), minLines = 2, maxLines = 5)
        Spacer(Modifier.height(13.dp))
        PhotoControls(vm, onCamera, onGallery)
        Spacer(Modifier.height(13.dp))
        Button(onClick = { vm.queueEvidence(id, comment) }, modifier = Modifier.fillMaxWidth()) {
            Text("Guardar evidencia pendiente")
        }
        Spacer(Modifier.height(7.dp))
        Text("Imagen JPEG hasta 5 MB. SHA-256 verificado por el servidor al sincronizar.",
            color = Muted, fontSize = 11.sp)
    }
}

@Composable private fun QueueView(vm: OrviaViewModel) {
    Title("SINCRONIZACIÓN", "Operaciones pendientes",
        "Nada se marca como confirmado hasta que lo acepta el servidor.")
    Box(Modifier.fillMaxWidth().clip(cardShape).background(gradient).padding(22.dp)) {
        Column {
            Text("COLA CIFRADA EN ESTE DISPOSITIVO", color = Color(0xFFC4F1E0),
                letterSpacing = 1.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            Text("${vm.pending.size}", fontSize = 40.sp, color = Color.White,
                fontWeight = FontWeight.ExtraBold)
            Text("Operaciones almacenadas localmente", color = Color.White)
            Spacer(Modifier.height(16.dp))
            Button(onClick = vm::syncQueue, enabled = !vm.syncing &&
                vm.pending.any { it.status in listOf("pendiente", "reintentar") },
                colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = Forest),
                modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Outlined.CloudUpload, contentDescription = null)
                Spacer(Modifier.width(8.dp)); Text("Sincronizar ahora", fontWeight = FontWeight.Bold)
            }
        }
    }
    Spacer(Modifier.height(18.dp))
    if (vm.pending.isEmpty()) {
        OrviaCard {
            Icon(Icons.Outlined.CloudDone, contentDescription = null, tint = Forest,
                modifier = Modifier.size(34.dp))
            Spacer(Modifier.height(9.dp))
            Text("No hay operaciones pendientes", fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(6.dp))
            Text("Cuando guardes una captura offline aparecerá aquí. Las aceptadas desaparecen de la cola.",
                color = Muted, fontSize = 12.sp)
        }
    }
    vm.pending.forEach { item ->
        OrviaCard {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(when(item.type) {
                    "evidencia" -> Icons.Outlined.CameraAlt
                    "recepcion" -> Icons.Outlined.Inventory2
                    else -> Icons.Outlined.LocalShipping
                }, contentDescription = null, tint = Forest)
                Spacer(Modifier.width(9.dp))
                Column(Modifier.weight(1f)) {
                    Text(item.type.replace('_', ' '), fontWeight = FontWeight.Bold)
                    Text(item.capturedAt.take(19).replace('T',' '), color = Muted, fontSize = 11.sp)
                }
                Surface(color = if(item.status == "conflicto" || item.status == "rechazada")
                    Color(0xFFFFEEE9) else EmeraldSoft, shape = RoundedCornerShape(13.dp)) {
                    Text(item.status, color = if(item.status in listOf("conflicto","rechazada"))
                        Color(0xFF9A4035) else Forest, fontSize = 10.sp,
                        modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp))
                }
            }
            Spacer(Modifier.height(8.dp))
            Text("UUID: ${item.id.take(8)}…", color = Muted, fontSize = 11.sp)
            if (item.detail.isNotBlank()) {
                Spacer(Modifier.height(7.dp)); Text(item.detail, color = Color(0xFF9A4035), fontSize = 11.sp)
            }
            Spacer(Modifier.height(8.dp))
            TextButton(onClick = { vm.deleteQueued(item.id) }) {
                Icon(Icons.Outlined.DeleteOutline, contentDescription = null,
                    modifier = Modifier.size(17.dp))
                Spacer(Modifier.width(6.dp)); Text("Quitar de mi dispositivo")
            }
        }
        Spacer(Modifier.height(10.dp))
    }
}

@Composable private fun ProfileView(vm: OrviaViewModel) {
    val s = vm.session ?: return
    Title("MI CUENTA", "Perfil y seguridad", "Las autorizaciones se verifican en el servidor.")
    OrviaCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(54.dp).clip(RoundedCornerShape(17.dp)).background(EmeraldSoft),
                contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.PersonOutline, contentDescription = null, tint = Forest,
                    modifier = Modifier.size(28.dp))
            }
            Spacer(Modifier.width(13.dp))
            Column {
                Text(s.name, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp)
                Text(s.email, color = Muted, fontSize = 12.sp)
            }
        }
        HorizontalDivider(Modifier.padding(vertical = 14.dp), color = Border)
        KeyValue("Rol", s.role)
        Spacer(Modifier.height(10.dp))
        KeyValue("Usuario", "#${s.id}")
        Spacer(Modifier.height(10.dp))
        KeyValue("Servidor", vm.host)
        Spacer(Modifier.height(20.dp))
        OutlinedButton(onClick = vm::logout, modifier = Modifier.fillMaxWidth(), enabled = !vm.busy) {
            Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = null, modifier = Modifier.size(17.dp))
            Spacer(Modifier.width(8.dp)); Text("Cerrar sesión")
        }
    }
    Spacer(Modifier.height(15.dp))
    OrviaCard {
        Text("Seguridad por diseño", fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(10.dp))
        Text("• Tokens y cola cifrados con Android Keystore.\n" +
            "• Permisos JWT comprobados por los microservicios.\n" +
            "• En producción se exige HTTPS.\n" +
            "• Las operaciones financieras no entran a la cola offline.",
            fontSize = 12.sp, color = Muted, lineHeight = 19.sp)
    }
    Spacer(Modifier.height(13.dp))
    Text("Avisos push y correo requieren el futuro servicio de notificaciones; no están simulados en esta app.",
        color = Muted, fontSize = 11.sp)
}

@Composable private fun KeyValue(label: String, value: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = Muted, fontSize = 12.sp, modifier = Modifier.width(85.dp))
        Text(value, fontWeight = FontWeight.Medium, fontSize = 12.sp,
            modifier = Modifier.weight(1f))
    }
}

@Composable private fun AlertsView(vm: OrviaViewModel) {
    Title("MONITOREO", "Alertas operativas", "Alertas reales de Orvia a través del acceso seguro. No son notificaciones push.")
    OutlinedButton(onClick = vm::refreshData, enabled = !vm.busy,
        modifier = Modifier.fillMaxWidth()) {
        Icon(Icons.Outlined.Refresh, contentDescription = null)
        Spacer(Modifier.width(8.dp)); Text("Actualizar alertas")
    }
    Spacer(Modifier.height(14.dp))
    if (vm.monitorAlerts.isEmpty()) {
        OrviaCard {
            Text("No se recibieron alertas activas", fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(6.dp))
            Text("También puede indicar que el servicio no está disponible. Comprueba /servicios/integraciones-monitoreo/health.",
                color = Muted, fontSize = 12.sp)
        }
    }
    vm.monitorAlerts.forEach { alert ->
        OrviaCard {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.WarningAmber, contentDescription = null, tint = Amber)
                Spacer(Modifier.width(9.dp))
                Text(alert.optString("tipo", "Alerta operativa"), fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(6.dp))
            val message = alert.optString("mensaje").ifBlank {
                alert.optString("descripcion").ifBlank { alert.optString("detalle", "Revisa el monitoreo web") }
            }
            Text(message, color = Muted, fontSize = 12.sp)
            Spacer(Modifier.height(7.dp))
            Text("Estado: ${alert.optString("estado", "activa")}", color = Amber, fontSize = 11.sp)
        }
        Spacer(Modifier.height(10.dp))
    }
}
