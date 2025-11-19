package com.encuestas.api.service;

import com.encuestas.api.model.Usuario;
import com.encuestas.api.repository.UsuarioRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class UsuarioService {
    
    @Autowired
    private UsuarioRepository usuarioRepository;
    
    public List<Usuario> obtenerTodos() {
        return usuarioRepository.findAll();
    }
    
    public Optional<Usuario> obtenerPorId(Integer id) {
        return usuarioRepository.findById(id);
    }
    
    public Usuario crear(Usuario usuario) {
        return usuarioRepository.save(usuario);
    }
    
    public Usuario actualizar(Integer id, Usuario usuarioActualizado) {
        Optional<Usuario> usuario = usuarioRepository.findById(id);
        if (usuario.isPresent()) {
            Usuario u = usuario.get();
            if (usuarioActualizado.getNombre() != null) u.setNombre(usuarioActualizado.getNombre());
            if (usuarioActualizado.getApellidos() != null) u.setApellidos(usuarioActualizado.getApellidos());
            if (usuarioActualizado.getEmail() != null) u.setEmail(usuarioActualizado.getEmail());
            if (usuarioActualizado.getTelefono() != null) u.setTelefono(usuarioActualizado.getTelefono());
            if (usuarioActualizado.getGenero() != null) u.setGenero(usuarioActualizado.getGenero());
            return usuarioRepository.save(u);
        }
        return null;
    }
    
    public boolean eliminar(Integer id) {
        if (usuarioRepository.existsById(id)) {
            usuarioRepository.deleteById(id);
            return true;
        }
        return false;
    }
}
