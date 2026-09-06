-- =============================================================================
-- Migracion 006: validaciones de reembolso y refuerzo del trigger de destino
-- Motivo:
--   (a) Nada impedia registrar un reembolso mayor al valor de lo que se compro,
--       lo que es un hueco de fraude abierto justo en el proceso que RF-25
--       pretende vigilar.
--   (b) RN-04 exige que el reembolso solo se apruebe sobre una devolucion ya
--       autorizada, y eso no estaba forzado en la base de datos.
--   (c) El trigger del esquema base solo revisaba al insertar o actualizar la
--       disposicion. Si la inspeccion cambiaba despues a "no apto", una
--       disposicion previa con destino 'inventario' quedaba en contradiccion
--       con RN-06 y RN-07.
-- Trazabilidad: RN-03, RN-04, RN-06, RN-07, RF-20, RF-21, RF-25
-- =============================================================================

-- (a) y (b): el reembolso no puede exceder el valor devuelto ni aprobarse sobre
-- una devolucion que no fue autorizada.
CREATE OR REPLACE FUNCTION fn_validar_reembolso()
RETURNS TRIGGER AS $$
DECLARE
    v_estado    VARCHAR(30);
    v_maximo    NUMERIC(10, 2);
BEGIN
    SELECT d.estado,
           vd.precio_unitario * d.cantidad_devuelta
      INTO v_estado, v_maximo
      FROM devoluciones d
      JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
     WHERE d.id = NEW.devolucion_id;

    IF v_estado IS NULL THEN
        RAISE EXCEPTION 'No existe la devolucion % para registrar el reembolso.', NEW.devolucion_id;
    END IF;

    -- RN-04: solo sobre devoluciones que ya pasaron por autorizacion.
    IF NEW.estado = 'aprobado' AND v_estado IN ('solicitada', 'en_revision', 'rechazada') THEN
        RAISE EXCEPTION
            'No se puede aprobar el reembolso de la devolucion %: su estado es "%" y aun no ha sido autorizada (RN-04).',
            NEW.devolucion_id, v_estado;
    END IF;

    -- Limite superior: lo que realmente se pago por lo devuelto.
    IF NEW.monto > v_maximo THEN
        RAISE EXCEPTION
            'El reembolso de la devolucion % (%) excede el valor de lo devuelto (%). Revisar posible fraude (RF-25).',
            NEW.devolucion_id, NEW.monto, v_maximo;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_reembolso
    BEFORE INSERT OR UPDATE ON reembolsos
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_reembolso();

-- (c) Trigger reciproco: si la inspeccion pasa a "no apto", no puede quedar en
-- pie una disposicion que ya mando el producto a inventario.
CREATE OR REPLACE FUNCTION fn_validar_inspeccion_vs_disposicion()
RETURNS TRIGGER AS $$
DECLARE
    v_destino VARCHAR(30);
BEGIN
    IF NEW.apto_para_inventario = FALSE THEN
        SELECT destino INTO v_destino
          FROM disposiciones
         WHERE devolucion_id = NEW.devolucion_id;

        IF v_destino = 'inventario' THEN
            RAISE EXCEPTION
                'La devolucion % ya tiene destino "inventario". Corrija la disposicion antes de marcar el producto como no apto (RN-06, RN-07).',
                NEW.devolucion_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_inspeccion_vs_disposicion
    BEFORE UPDATE ON inspecciones_ref
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_inspeccion_vs_disposicion();
