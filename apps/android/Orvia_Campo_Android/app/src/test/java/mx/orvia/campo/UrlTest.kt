package mx.orvia.campo

import mx.orvia.campo.network.OrviaApi
import org.junit.Assert.assertFalse
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class UrlTest {
    private val api = OrviaApi()
    @Test fun aceptaHostsCorrectos() {
        assertTrue(api.hostValid("http://10.0.2.2"))
        assertTrue(api.hostValid("https://orvia.empresa.mx"))
    }
    @Test fun rechazaHostsConPuertoRutaCredenciales() {
        assertFalse(api.hostValid("http://10.0.2.2:8001"))
        assertFalse(api.hostValid("https://orvia.mx/path"))
        assertFalse(api.hostValid("http://usuario:clave@orvia.mx"))
    }
    @Test fun construyeRutaSinPuertosDeMicroservicios() {
        assertEquals("https://orvia.empresa.mx/api/v1/auth/login",
            api.url("https://orvia.empresa.mx", "/api/v1/auth/login"))
    }
}
