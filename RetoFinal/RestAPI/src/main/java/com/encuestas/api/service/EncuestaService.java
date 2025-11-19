package com.encuestas.api.service;

import com.encuestas.api.model.Encuesta;
import com.encuestas.api.repository.EncuestaRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class EncuestaService {
    
    @Autowired
    private EncuestaRepository encuestaRepository;
    
    public List<Encuesta> obtenerTodas() {
        return encuestaRepository.findAll();
    }
    
    public Optional<Encuesta> obtenerPorId(Integer id) {
        return encuestaRepository.findById(id);
    }
    
    public Encuesta crear(Encuesta encuesta) {
        encuesta.setFechaCreacion(LocalDateTime.now());
        encuesta.setEstatus(true);
        return encuestaRepository.save(encuesta);
    }
    
    public Encuesta actualizar(Integer id, Encuesta encuestaActualizada) {
        Optional<Encuesta> encuesta = encuestaRepository.findById(id);
        if (encuesta.isPresent()) {
            Encuesta e = encuesta.get();
            if (encuestaActualizada.getTitulo() != null) e.setTitulo(encuestaActualizada.getTitulo());
            if (encuestaActualizada.getDescripcion() != null) e.setDescripcion(encuestaActualizada.getDescripcion());
            if (encuestaActualizada.getEstatus() != null) e.setEstatus(encuestaActualizada.getEstatus());
            return encuestaRepository.save(e);
        }
        return null;
    }
    
    public boolean eliminar(Integer id) {
        if (encuestaRepository.existsById(id)) {
            encuestaRepository.deleteById(id);
            return true;
        }
        return false;
    }
}
