from pathlib import Path

raiz = Path(SPECPATH).parents[1]
datos = [
    (str(raiz / "apps/escritorio/config.example.json"), "apps/escritorio"),
    (str(raiz / "apps/escritorio/assets/orvia-hoja.png"), "apps/escritorio/assets"),
]
for patron in (
    "shared/contratos/*.xsd",
    "services/auth/contratos/*.xsd",
    "services/inspecciones/contratos/*.xsd",
    "services/disposicion_inventario/contratos/*.xsd",
    "services/reembolsos_costos/contratos/*.xsd",
):
    for archivo in raiz.glob(patron):
        datos.append((str(archivo), str(archivo.parent.relative_to(raiz))))

a = Analysis(
    [str(raiz / "apps/escritorio/main.py")],
    pathex=[str(raiz / "apps/escritorio")],
    binaries=[],
    datas=datos,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CentroDevoluciones",
    icon=str(raiz / "apps/escritorio/assets/orvia.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
