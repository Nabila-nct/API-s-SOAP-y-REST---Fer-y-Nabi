package com.encuestas.api.controller;

import com.encuestas.api.model.Usuario;
import com.encuestas.api.service.UsuarioService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/usuarios")
@CrossOrigin(origins = "*")
public class UsuarioController {
    
    @Autowired
    private UsuarioService usuarioService;
    
    @GetMapping
    public ResponseEntity<List<Usuario>> obtenerTodos() {
        List<Usuario> usuarios = usuarioService.obtenerTodos();
        return ResponseEntity.ok(usuarios);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<?> obtenerPorId(@PathVariable Integer id) {
        Optional<Usuario> usuario = usuarioService.obtenerPorId(id);
        if (usuario.isPresent()) {
            return ResponseEntity.ok(usuario.get());
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("Usuario no encontrado"));
    }
    
    @PostMapping
    public ResponseEntity<?> crear(@RequestBody Usuario usuario) {
        if (usuario.getNombre() == null || usuario.getNombre().isEmpty() ||
            usuario.getApellidos() == null || usuario.getApellidos().isEmpty() ||
            usuario.getEmail() == null || usuario.getEmail().isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(new ErrorResponse("Nombre, apellidos y email son obligatorios"));
        }
        Usuario nuevoUsuario = usuarioService.crear(usuario);
        return ResponseEntity.status(HttpStatus.CREATED).body(nuevoUsuario);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<?> actualizar(@PathVariable Integer id, @RequestBody Usuario usuarioActualizado) {
        Usuario usuario = usuarioService.actualizar(id, usuarioActualizado);
        if (usuario != null) {
            return ResponseEntity.ok(usuario);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("Usuario no encontrado"));
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<?> eliminar(@PathVariable Integer id) {
        if (usuarioService.eliminar(id)) {
            return ResponseEntity.ok(new SuccessResponse("Usuario eliminado correctamente"));
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("Usuario no encontrado"));
    }
    
    // Clases auxiliares
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
