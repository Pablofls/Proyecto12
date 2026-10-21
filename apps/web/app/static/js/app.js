// Comportamiento compartido de la interfaz.

// Boton para mostrar u ocultar una contrasena. Se aplica a cualquier
// .campo-password de la pagina, sin importar en que formulario este.
document.addEventListener('click', function (evento) {
  const boton = evento.target.closest('.ver-password');
  if (!boton) return;

  const campo = boton.closest('.campo-password').querySelector('input');
  const ojo = boton.querySelector('.icono-ojo');
  const ojoTachado = boton.querySelector('.icono-ojo-tachado');

  const visible = campo.type === 'text';
  campo.type = visible ? 'password' : 'text';

  // Se usa una clase y no el atributo hidden: ese atributo no oculta elementos
  // SVG, porque la regla del navegador que lo aplica solo alcanza a los
  // elementos del espacio de nombres HTML.
  ojo.classList.toggle('oculto', !visible);
  ojoTachado.classList.toggle('oculto', visible);

  const etiqueta = visible ? 'Mostrar contrasena' : 'Ocultar contrasena';
  boton.setAttribute('aria-label', etiqueta);
  boton.setAttribute('title', etiqueta);
  boton.setAttribute('aria-pressed', String(!visible));
  campo.focus();
});

// Campanita de notificaciones (RF-29, UC-25): sondeo ligero cada 30 s al
// endpoint JSON. Sin sondeo en pestanas ocultas para no cargar el servidor.
(function () {
  const campanita = document.querySelector('.campanita');
  if (!campanita) return;

  const boton = campanita.querySelector('.campanita-boton');
  const insignia = campanita.querySelector('.campanita-insignia');
  const panel = campanita.querySelector('.campanita-panel');
  const lista = campanita.querySelector('.campanita-lista');

  function pintar(datos) {
    insignia.textContent = datos.no_leidas > 99 ? '99+' : String(datos.no_leidas);
    insignia.hidden = datos.no_leidas === 0;

    lista.replaceChildren();
    if (!datos.ultimas.length) {
      const vacio = document.createElement('li');
      vacio.className = 'vacio';
      vacio.textContent = 'No tienes notificaciones.';
      lista.appendChild(vacio);
      return;
    }
    datos.ultimas.forEach(function (n) {
      const item = document.createElement('li');
      if (!n.leido) item.className = 'no-leida';
      const formulario = document.createElement('form');
      formulario.method = 'post';
      formulario.action = n.leer;
      const enlace = document.createElement('button');
      enlace.type = 'submit';
      // textContent y no innerHTML: el mensaje es texto, nunca marcado.
      enlace.textContent = n.mensaje;
      const cuando = document.createElement('span');
      cuando.className = 'cuando';
      cuando.textContent = n.fecha;
      enlace.appendChild(cuando);
      formulario.appendChild(enlace);
      item.appendChild(formulario);
      lista.appendChild(item);
    });
  }

  function actualizar() {
    if (document.hidden) return;
    fetch(campanita.dataset.resumen, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (datos) { if (datos) pintar(datos); })
      .catch(function () { /* sin red: se reintenta en el siguiente ciclo */ });
  }

  function alternar(abrir) {
    panel.hidden = !abrir;
    boton.setAttribute('aria-expanded', String(abrir));
  }

  boton.addEventListener('click', function (evento) {
    evento.preventDefault();
    if (panel.hidden) actualizar();
    alternar(panel.hidden);
  });
  document.addEventListener('click', function (evento) {
    if (!campanita.contains(evento.target)) alternar(false);
  });
  document.addEventListener('keydown', function (evento) {
    if (evento.key === 'Escape') alternar(false);
  });
  document.addEventListener('visibilitychange', actualizar);

  actualizar();
  setInterval(actualizar, 30000);
})();
