from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn

# Crear instancia de FastAPI
app = FastAPI(
    title="Synco API",
    description="API REST con FastAPI para Synco",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool = True

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool

class MessageResponse(BaseModel):
    message: str
    status: str

# Base de datos en memoria (para ejemplo)
items_db: List[Item] = [
    Item(id=1, name="Producto 1", description="Descripción del producto 1", price=29.99),
    Item(id=2, name="Producto 2", description="Descripción del producto 2", price=49.99),
]

# Rutas de la API

@app.get("/", response_model=MessageResponse)
async def root():
    """Endpoint raíz de la API"""
    return MessageResponse(
        message="¡Bienvenido a Synco API!",
        status="success"
    )

@app.get("/health", response_model=MessageResponse)
async def health_check():
    """Endpoint para verificar el estado de la API"""
    return MessageResponse(
        message="API funcionando correctamente",
        status="healthy"
    )

@app.get("/items", response_model=List[ItemResponse])
async def get_items():
    """Obtener todos los items"""
    return items_db

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Obtener un item específico por ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item no encontrado")

@app.post("/items", response_model=ItemResponse)
async def create_item(item: Item):
    """Crear un nuevo item"""
    # Generar nuevo ID
    new_id = max([i.id for i in items_db], default=0) + 1
    item.id = new_id
    items_db.append(item)
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: Item):
    """Actualizar un item existente"""
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            item.id = item_id
            items_db[i] = item
            return item
    raise HTTPException(status_code=404, detail="Item no encontrado")

@app.delete("/items/{item_id}", response_model=MessageResponse)
async def delete_item(item_id: int):
    """Eliminar un item"""
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(i)
            return MessageResponse(
                message=f"Item {item_id} eliminado correctamente",
                status="success"
            )
    raise HTTPException(status_code=404, detail="Item no encontrado")

# Función para ejecutar localmente
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
