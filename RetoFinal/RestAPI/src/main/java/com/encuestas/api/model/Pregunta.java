package com.encuestas.api.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Entity
@Table(name = "preguntas")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Pregunta {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_pregunta")
    private Integer idPregunta;
    
    @Column(name = "id_encuesta", nullable = false)
    private Integer idEncuesta;
    
    @Column(name = "text_pregunta", columnDefinition = "TEXT", nullable = false)
    private String textPregunta;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_encuesta", insertable = false, updatable = false)
    private Encuesta encuesta;
    
    @OneToMany(mappedBy = "pregunta", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Respuesta> respuestas;
}
