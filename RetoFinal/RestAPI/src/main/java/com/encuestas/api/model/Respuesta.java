package com.encuestas.api.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "respuestas")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Respuesta {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_respuesta")
    private Integer idRespuesta;
    
    @Column(name = "id_pregunta", nullable = false)
    private Integer idPregunta;
    
    @Column(name = "id_usuario", nullable = false)
    private Integer idUsuario;
    
    @Column(name = "texto_respuesta", columnDefinition = "TEXT", nullable = false)
    private String textoRespuesta;
    
    @Column(name = "fecha_registrada", nullable = false, columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    private LocalDateTime fechaRegistrada;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_pregunta", insertable = false, updatable = false)
    private Pregunta pregunta;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_usuario", insertable = false, updatable = false)
    private Usuario usuario;
}
