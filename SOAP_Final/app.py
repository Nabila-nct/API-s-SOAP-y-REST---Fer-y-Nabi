import logging
from datetime import datetime
import os
from urllib.parse import urlsplit, urlunsplit
from sqlalchemy import text

# Para el servicio SOAP
from spyne import Application, rpc, ServiceBase, Integer, Unicode, Boolean, ComplexModel, Fault
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

# Para la Base de Datos (ORM)
from sqlalchemy import create_engine, Column, Integer as SqlInteger, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session

logging.basicConfig(level=logging.INFO)
logging.getLogger('spyne.protocol.xml').setLevel(logging.INFO)

# --- 1. Configuración de Base de Datos (SQLAlchemy) ---

# URL de la base de datos: preferir la variable de entorno DATABASE_URL.
# Si no está definida, usar SQLite local para desarrollo.
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # fallback a SQLite local para desarrollo
    DATABASE_URL = 'sqlite:///./dev.db'
    logging.info('DATABASE_URL no encontrada en el entorno: usando SQLite local para desarrollo')
else:
    # Si el usuario pasó una URL con esquema mysql:// cambiaremos al adaptador pymysql
    if DATABASE_URL.startswith('mysql://'):
        DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)

# Para SQLite algunos adaptadores requieren connect_args
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)


def _mask_db_url(url: str) -> str:
    """Devuelve una versión enmascarada de la URL (oculta la contraseña)."""
    try:
        parts = urlsplit(url)
        if parts.password:
            # reconstruir netloc con password oculta
            user = parts.username or ''
            host = parts.hostname or ''
            port = f":{parts.port}" if parts.port else ''
            netloc = f"{user}:***@{host}{port}"
        else:
            netloc = parts.netloc
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        # Si falla el parseo, devolver versión truncada
        return (url[:80] + '...') if len(url) > 80 else url


def _check_db_connection(engine, url):
    masked = _mask_db_url(url)
    if url.startswith('sqlite'):
        logging.info(f"Usando base de datos local: {masked}")
        return True

    logging.info(f"Probando conexión a la base de datos remota: {masked}")
    try:
        with engine.connect() as conn:
            # Usar text(...) para SQLAlchemy 1.4+/2.0
            conn.execute(text('SELECT 1'))
        logging.info("Conexión a la base de datos remota OK")
        return True
    except Exception as e:
        logging.exception(f"No se pudo conectar a la base de datos remota: {masked}")
        return False
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def safe_commit(db: Session):
    """Commit seguro: hace rollback y convierte errores en Fault legible para SOAP."""
    try:
        db.commit()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            logging.exception('Error haciendo rollback tras excepción en commit')
        logging.exception('Error en commit de la base de datos')
        # Lanzar un Fault para que el cliente SOAP reciba un mensaje entendible
        raise Fault(faultcode='Server', faultstring=f'Error en la base de datos: {str(e)}')


# --- 2. Modelos de la Base de Datos (SQLAlchemy) ---


class EncuestaDB(Base):
    __tablename__ = 'surveys'

    id_encuesta = Column(SqlInteger, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=True)
    descripcion = Column(String(255), nullable=True)
    estatus = Column(SqlInteger, nullable=True)
    fecha_creacion = Column(DateTime, nullable=True)


class PreguntaDB(Base):
    __tablename__ = 'questions'

    id_pregunta = Column(SqlInteger, primary_key=True, autoincrement=True)
    # la columna en la BD existente se llama `id_encuesta`
    id_encuesta = Column(SqlInteger, ForeignKey('surveys.id_encuesta'), nullable=False)
    # en la tabla actual el campo de texto es `text_pregunta`
    texto_pregunta = Column('text_pregunta', String(255), nullable=True)


class RespuestaDB(Base):
    __tablename__ = 'answers'

    id_respuesta = Column(SqlInteger, primary_key=True, autoincrement=True)
    id_pregunta = Column(SqlInteger, ForeignKey('questions.id_pregunta'), nullable=False)
    id_usuario = Column(SqlInteger, ForeignKey('users.id_usuario'), nullable=True)
    texto_respuesta = Column(String(255), nullable=True)
    fecha_registro = Column('fecha_registrada', DateTime, nullable=True)


class UsuarioDB(Base):
    __tablename__ = 'users'

    id_usuario = Column(SqlInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=True)
    apellidos = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, nullable=True)
    genero = Column(String(255), nullable=True)
    telefono = Column(String(255), nullable=True)


# --- 3. Modelos del API (Spyne) ---


class Encuesta(ComplexModel):
    __namespace__ = 'encuestas.soap.retofinal'

    id_encuesta = Integer
    titulo = Unicode
    descripcion = Unicode
    fecha_creacion = Unicode


class Pregunta(ComplexModel):
    __namespace__ = 'encuestas.soap.retofinal'

    id_pregunta = Integer
    id_encuesta = Integer
    texto_pregunta = Unicode


class Respuesta(ComplexModel):
    __namespace__ = 'encuestas.soap.retofinal'

    id_respuesta = Integer
    id_pregunta = Integer
    id_usuario = Integer
    texto_respuesta = Unicode
    fecha_registro = Unicode


class Usuario(ComplexModel):
    __namespace__ = 'encuestas.soap.retofinal'

    id_usuario = Integer
    nombre = Unicode
    apellidos = Unicode
    email = Unicode
    telefono = Unicode
    genero = Unicode


# --- 4. Definición del Servicio SOAP ---

class EncuestaService(ServiceBase):
    """Servicio SOAP que agrupa operaciones CRUD para encuestas, preguntas,
    respuestas y usuarios."""

    @staticmethod
    def _get_db(ctx):
        if not hasattr(ctx, 'udc') or ctx.udc is None:
            ctx.udc = type('UDC', (), {})()

        db = getattr(ctx.udc, 'db', None)
        if db is None:
            db = SessionLocal()
            ctx.udc.db = db
            return db, True
        return db, False

    # --- Encuestas ---
    @rpc(Encuesta, _returns=Encuesta, _body_style='wrapped', _out_variable_name='encuesta_creada')
    def crear_encuesta(ctx, encuesta: Encuesta):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not encuesta.titulo:
                raise ValueError("'titulo' es obligatorio para crear una encuesta")
            db_enc = EncuestaDB(titulo=encuesta.titulo, descripcion=encuesta.descripcion)
            db.add(db_enc)
            safe_commit(db)
            db.refresh(db_enc)
            return Encuesta(id_encuesta=db_enc.id_encuesta, titulo=db_enc.titulo, descripcion=db_enc.descripcion, fecha_creacion=str(db_enc.fecha_creacion))
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Encuesta, _body_style='wrapped')
    def obtener_encuesta(ctx, id_encuesta: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_enc = db.query(EncuestaDB).filter(EncuestaDB.id_encuesta == id_encuesta).first()
            if db_enc is None:
                raise ValueError(f"Encuesta no encontrada con id: {id_encuesta}")
            return Encuesta(id_encuesta=db_enc.id_encuesta, titulo=db_enc.titulo, descripcion=db_enc.descripcion, fecha_creacion=str(db_enc.fecha_creacion))
        finally:
            if close_after:
                db.close()

    @rpc(Encuesta, _returns=Encuesta, _body_style='wrapped')
    def actualizar_encuesta(ctx, encuesta_actualizada: Encuesta):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not encuesta_actualizada.id_encuesta:
                raise ValueError("'id_encuesta' es requerido para actualizar")
            db_enc = db.query(EncuestaDB).filter(EncuestaDB.id_encuesta == encuesta_actualizada.id_encuesta).first()
            if db_enc is None:
                raise ValueError(f"Encuesta no encontrada con id: {encuesta_actualizada.id_encuesta}")
            db_enc.titulo = encuesta_actualizada.titulo
            db_enc.descripcion = encuesta_actualizada.descripcion
            safe_commit(db)
            db.refresh(db_enc)
            return Encuesta(id_encuesta=db_enc.id_encuesta, titulo=db_enc.titulo, descripcion=db_enc.descripcion, fecha_creacion=str(db_enc.fecha_creacion))
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Boolean, _body_style='wrapped')
    def eliminar_encuesta(ctx, id_encuesta: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_enc = db.query(EncuestaDB).filter(EncuestaDB.id_encuesta == id_encuesta).first()
            if db_enc is None:
                raise ValueError(f"Encuesta no encontrada con id: {id_encuesta}")
            db.delete(db_enc)
            safe_commit(db)
            return True
        finally:
            if close_after:
                db.close()

    # --- Preguntas ---
    @rpc(Pregunta, _returns=Pregunta, _body_style='wrapped')
    def crear_pregunta(ctx, pregunta: Pregunta):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not pregunta.texto_pregunta or not pregunta.id_encuesta:
                raise ValueError("'texto_pregunta' e 'id_encuesta' son obligatorios")
            # validar existencia de encuesta
            if db.query(EncuestaDB).filter(EncuestaDB.id_encuesta == pregunta.id_encuesta).first() is None:
                raise ValueError(f"Encuesta no encontrada con id: {pregunta.id_encuesta}")
            db_preg = PreguntaDB(id_encuesta=pregunta.id_encuesta, texto_pregunta=pregunta.texto_pregunta)
            db.add(db_preg)
            safe_commit(db)
            db.refresh(db_preg)
            return Pregunta(id_pregunta=db_preg.id_pregunta, id_encuesta=db_preg.id_encuesta, texto_pregunta=db_preg.texto_pregunta)
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Pregunta, _body_style='wrapped')
    def obtener_pregunta(ctx, id_pregunta: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_preg = db.query(PreguntaDB).filter(PreguntaDB.id_pregunta == id_pregunta).first()
            if db_preg is None:
                raise ValueError(f"Pregunta no encontrada con id: {id_pregunta}")
            return Pregunta(id_pregunta=db_preg.id_pregunta, id_encuesta=db_preg.id_encuesta, texto_pregunta=db_preg.texto_pregunta)
        finally:
            if close_after:
                db.close()

    @rpc(Pregunta, _returns=Pregunta, _body_style='wrapped')
    def actualizar_pregunta(ctx, pregunta_actualizada: Pregunta):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not pregunta_actualizada.id_pregunta:
                raise ValueError("'id_pregunta' es requerido para actualizar")
            db_preg = db.query(PreguntaDB).filter(PreguntaDB.id_pregunta == pregunta_actualizada.id_pregunta).first()
            if db_preg is None:
                raise ValueError(f"Pregunta no encontrada con id: {pregunta_actualizada.id_pregunta}")
            db_preg.texto_pregunta = pregunta_actualizada.texto_pregunta
            db_preg.id_encuesta = pregunta_actualizada.id_encuesta
            safe_commit(db)
            db.refresh(db_preg)
            return Pregunta(id_pregunta=db_preg.id_pregunta, id_encuesta=db_preg.id_encuesta, texto_pregunta=db_preg.texto_pregunta)
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Boolean, _body_style='wrapped')
    def eliminar_pregunta(ctx, id_pregunta: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_preg = db.query(PreguntaDB).filter(PreguntaDB.id_pregunta == id_pregunta).first()
            if db_preg is None:
                raise ValueError(f"Pregunta no encontrada con id: {id_pregunta}")
            db.delete(db_preg)
            safe_commit(db)
            return True
        finally:
            if close_after:
                db.close()

    # --- Usuarios ---
    @rpc(Usuario, _returns=Usuario, _body_style='wrapped')
    def crear_usuario(ctx, usuario: Usuario):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not usuario.nombre:
                raise ValueError("'nombre' es obligatorio para crear un usuario")
            db_usr = UsuarioDB(nombre=usuario.nombre, apellidos=usuario.apellidos, email=usuario.email, telefono=usuario.telefono, genero=usuario.genero)
            db.add(db_usr)
            safe_commit(db)
            db.refresh(db_usr)
            return Usuario(id_usuario=db_usr.id_usuario, nombre=db_usr.nombre, apellidos=db_usr.apellidos, email=db_usr.email, telefono=db_usr.telefono, genero=db_usr.genero)
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Usuario, _body_style='wrapped')
    def obtener_usuario(ctx, id_usuario: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_usr = db.query(UsuarioDB).filter(UsuarioDB.id_usuario == id_usuario).first()
            if db_usr is None:
                raise ValueError(f"Usuario no encontrado con id: {id_usuario}")
            return Usuario(id_usuario=db_usr.id_usuario, nombre=db_usr.nombre, apellidos=db_usr.apellidos, email=db_usr.email, telefono=db_usr.telefono, genero=db_usr.genero)
        finally:
            if close_after:
                db.close()

    @rpc(Usuario, _returns=Usuario, _body_style='wrapped')
    def actualizar_usuario(ctx, usuario_actualizado: Usuario):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not usuario_actualizado.id_usuario:
                raise ValueError("'id_usuario' es requerido para actualizar")
            db_usr = db.query(UsuarioDB).filter(UsuarioDB.id_usuario == usuario_actualizado.id_usuario).first()
            if db_usr is None:
                raise ValueError(f"Usuario no encontrado con id: {usuario_actualizado.id_usuario}")
            db_usr.nombre = usuario_actualizado.nombre
            db_usr.apellidos = usuario_actualizado.apellidos
            db_usr.email = usuario_actualizado.email
            db_usr.telefono = usuario_actualizado.telefono
            db_usr.genero = usuario_actualizado.genero
            safe_commit(db)
            db.refresh(db_usr)
            return Usuario(id_usuario=db_usr.id_usuario, nombre=db_usr.nombre, apellidos=db_usr.apellidos, email=db_usr.email, telefono=db_usr.telefono, genero=db_usr.genero)
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Boolean, _body_style='wrapped')
    def eliminar_usuario(ctx, id_usuario: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_usr = db.query(UsuarioDB).filter(UsuarioDB.id_usuario == id_usuario).first()
            if db_usr is None:
                raise ValueError(f"Usuario no encontrado con id: {id_usuario}")
            db.delete(db_usr)
            safe_commit(db)
            return True
        finally:
            if close_after:
                db.close()

    # --- Respuestas ---
    @rpc(Respuesta, _returns=Respuesta, _body_style='wrapped')
    def crear_respuesta(ctx, respuesta: Respuesta):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not respuesta.texto_respuesta or not respuesta.id_pregunta:
                raise ValueError("'texto_respuesta' e 'id_pregunta' son obligatorios")
            if db.query(PreguntaDB).filter(PreguntaDB.id_pregunta == respuesta.id_pregunta).first() is None:
                raise ValueError(f"Pregunta no encontrada con id: {respuesta.id_pregunta}")
            # usuario opcional
            db_res = RespuestaDB(id_pregunta=respuesta.id_pregunta, id_usuario=respuesta.id_usuario, texto_respuesta=respuesta.texto_respuesta)
            db.add(db_res)
            safe_commit(db)
            db.refresh(db_res)
            return Respuesta(id_respuesta=db_res.id_respuesta, id_pregunta=db_res.id_pregunta, id_usuario=db_res.id_usuario, texto_respuesta=db_res.texto_respuesta, fecha_registro=str(db_res.fecha_registro))
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Respuesta, _body_style='wrapped')
    def obtener_respuesta(ctx, id_respuesta: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_res = db.query(RespuestaDB).filter(RespuestaDB.id_respuesta == id_respuesta).first()
            if db_res is None:
                raise ValueError(f"Respuesta no encontrada con id: {id_respuesta}")
            return Respuesta(id_respuesta=db_res.id_respuesta, id_pregunta=db_res.id_pregunta, id_usuario=db_res.id_usuario, texto_respuesta=db_res.texto_respuesta, fecha_registro=str(db_res.fecha_registro))
        finally:
            if close_after:
                db.close()

    @rpc(Respuesta, _returns=Respuesta, _body_style='wrapped')
    def actualizar_respuesta(ctx, respuesta_actualizada: Respuesta):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            if not respuesta_actualizada.id_respuesta:
                raise ValueError("'id_respuesta' es requerido para actualizar")
            db_res = db.query(RespuestaDB).filter(RespuestaDB.id_respuesta == respuesta_actualizada.id_respuesta).first()
            if db_res is None:
                raise ValueError(f"Respuesta no encontrada con id: {respuesta_actualizada.id_respuesta}")
            db_res.texto_respuesta = respuesta_actualizada.texto_respuesta
            db_res.id_usuario = respuesta_actualizada.id_usuario
            safe_commit(db)
            db.refresh(db_res)
            return Respuesta(id_respuesta=db_res.id_respuesta, id_pregunta=db_res.id_pregunta, id_usuario=db_res.id_usuario, texto_respuesta=db_res.texto_respuesta, fecha_registro=str(db_res.fecha_registro))
        finally:
            if close_after:
                db.close()

    @rpc(Integer, _returns=Boolean, _body_style='wrapped')
    def eliminar_respuesta(ctx, id_respuesta: Integer):
        db, close_after = EncuestaService._get_db(ctx)
        try:
            db_res = db.query(RespuestaDB).filter(RespuestaDB.id_respuesta == id_respuesta).first()
            if db_res is None:
                raise ValueError(f"Respuesta no encontrada con id: {id_respuesta}")
            db.delete(db_res)
            safe_commit(db)
            return True
        finally:
            if close_after:
                db.close()


# --- 5. Creación de la Aplicación y Servidor ---

# Creamos las tablas en la BD (usando Base, que conoce a PreguntaDB)
# Comprobación de conexión a la BD y mensaje claro al iniciar
if _check_db_connection(engine, DATABASE_URL):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logging.exception("Error creando tablas en la base de datos")
else:
    logging.warning("Continuando sin crear tablas (problema de conexión a la BD remota). Revisa DATABASE_URL o usa SQLite local.")

# Creamos la aplicación Spyne (que conoce a EncuestaService)
application = Application([EncuestaService],
    tns='encuestas.soap.retofinal',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

# Envolvemos la aplicación Spyne en un estándar WSGI
wsgi_application = WsgiApplication(application)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    
    server = make_server('0.0.0.0', 8000, wsgi_application)
    logging.info("Servidor SOAP iniciado en http://localhost:8000/")
    logging.info("WSDL disponible en: http://localhost:8000/?wsdl")
    server.serve_forever()