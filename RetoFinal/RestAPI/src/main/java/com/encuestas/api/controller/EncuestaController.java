package com.encuestas.api.controller;

import com.encuestas.api.model.Encuesta;
import com.encuestas.api.service.EncuestaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/encuestas")
@CrossOrigin(origins = "*")
public class EncuestaController {
    
    @Autowired
    private EncuestaService encuestaService;
    
    @GetMapping
    public ResponseEntity<List<Encuesta>> obtenerTodas() {
        List<Encuesta> encuestas = encuestaService.obtenerTodas();
        return ResponseEntity.ok(encuestas);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<?> obtenerPorId(@PathVariable Integer id) {
        Optional<Encuesta> encuesta = encuestaService.obtenerPorId(id);
        if (encuesta.isPresent()) {
            return ResponseEntity.ok(encuesta.get());
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("Encuesta no encontrada"));
    }
    
    @PostMapping
    public ResponseEntity<?> crear(@RequestBody Encuesta encuesta) {
        if (encuesta.getTitulo() == null || encuesta.getTitulo().isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(new ErrorResponse("El título es obligatorio"));
        }
        Encuesta nuevaEncuesta = encuestaService.crear(encuesta);
        return ResponseEntity.status(HttpStatus.CREATED).body(nuevaEncuesta);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<?> actualizar(@PathVariable Integer id, @RequestBody Encuesta encuestaActualizada) {
        Encuesta encuesta = encuestaService.actualizar(id, encuestaActualizada);
        if (encuesta != null) {
            return ResponseEntity.ok(encuesta);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("Encuesta no encontrada"));
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<?> eliminar(@PathVariable Integer id) {
        if (encuestaService.eliminar(id)) {
            return ResponseEntity.ok(new SuccessResponse("Encuesta eliminada correctamente"));
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("Encuesta no encontrada"));
    }
    
    // Clases auxiliares para respuestas
    static class ErrorResponse {
        public String error;
        
        public ErrorResponse(String error) {
            this.error = error;
        }
    }
    
    static class SuccessResponse {
        public String mensaje;
        
        public SuccessResponse(String mensaje) {
            this.mensaje = mensaje;
        }
    }
}
