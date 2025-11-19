# REST API - Encuestas (Java Spring Boot)

API REST para gestionar **Encuestas** y **Usuarios** conectada a MySQL en Railway.

## Requisitos

- **Java 17+**
- **Maven 3.6+**
- **Git**

## Instalación y Ejecución

1. **Navega a la carpeta del proyecto:**

```powershell
cd "c:\Users\filib\Documents\RetoFinal\RestAPI"
```

2. **Compila y empaqueta el proyecto:**

```powershell
mvn clean package
```

3. **Ejecuta la aplicación:**

```powershell
mvn spring-boot:run
```

O si prefieres ejecutar el JAR:

```powershell
java -jar target/rest-api-1.0.0.jar
```

La API estará disponible en `http://localhost:3000`

## Endpoints REST

### Encuestas

- **GET** `/api/encuestas` - Listar todas las encuestas
- **GET** `/api/encuestas/{id}` - Obtener encuesta por ID
- **POST** `/api/encuestas` - Crear nueva encuesta
  - Body: `{ "titulo": "...", "descripcion": "..." }`
- **PUT** `/api/encuestas/{id}` - Actualizar encuesta
  - Body: `{ "titulo": "...", "descripcion": "...", "estatus": true }`
- **DELETE** `/api/encuestas/{id}` - Eliminar encuesta

### Usuarios

- **GET** `/api/usuarios` - Listar todos los usuarios
- **GET** `/api/usuarios/{id}` - Obtener usuario por ID
- **POST** `/api/usuarios` - Crear nuevo usuario
  - Body: `{ "nombre": "Juan", "apellidos": "Pérez", "email": "juan@example.com", "telefono": "123456789", "genero": "M" }`
- **PUT** `/api/usuarios/{id}` - Actualizar usuario
- **DELETE** `/api/usuarios/{id}` - Eliminar usuario

## Ejemplos con PowerShell

```powershell
# Crear una encuesta
$body = @{ titulo='Encuesta 1'; descripcion='Primera encuesta' } | ConvertTo-Json
curl -Method POST -Uri http://localhost:3000/api/encuestas -Body $body -ContentType 'application/json'

# Obtener todas las encuestas
curl http://localhost:3000/api/encuestas

# Crear un usuario
$usuario = @{ nombre='Juan'; apellidos='Pérez'; email='juan@example.com'; genero='M' } | ConvertTo-Json
curl -Method POST -Uri http://localhost:3000/api/usuarios -Body $usuario -ContentType 'application/json'

# Obtener todos los usuarios
curl http://localhost:3000/api/usuarios
```

## Configuración

La conexión a la base de datos MySQL en Railway se configura automáticamente en `src/main/resources/application.properties`.

Conexión:
- **URL:** `jdbc:mysql://nozomi.proxy.rlwy.net:48991/railway`
- **Usuario:** `root`
- **Base de datos:** `railway`

## Estructura del Proyecto

```
RestAPI/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/encuestas/api/
│   │   │       ├── RestApiApplication.java
│   │   │       ├── controller/
│   │   │       ├── service/
│   │   │       ├── repository/
│   │   │       └── model/
│   │   └── resources/
│   │       └── application.properties
│   └── test/
└── README.md
```
