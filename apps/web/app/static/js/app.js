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
