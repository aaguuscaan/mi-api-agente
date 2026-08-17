# app/tools.py
import random
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

ORDENES = {
    102: [
        {"id": 1, "producto": "Laptop", "cantidad": 2, "precio": 3500, "fecha": "2024-08-10"},
        {"id": 2, "producto": "Teclado", "cantidad": 1, "precio": 200, "fecha": "2024-08-11"},
        {"id": 3, "producto": "Monitor", "cantidad": 1, "precio": 450, "fecha": "2024-08-12"},
    ],
    103: [
        {"id": 4, "producto": "Mouse", "cantidad": 3, "precio": 75, "fecha": "2024-08-09"},
    ],
    104: [
        {"id": 5, "producto": "Laptop", "cantidad": 1, "precio": 3500, "fecha": "2024-08-10"},
        {"id": 6, "producto": "Monitor", "cantidad": 2, "precio": 900, "fecha": "2024-08-13"},
    ]
}

class BuscarPedidosInput(BaseModel):
    cliente_id: int = Field(
        description="ID numérico del cliente para buscar sus pedidos",
        ge=1
    )
    limit: int = Field(
        default=5,
        description="Número máximo de pedidos a devolver (por defecto 5)"
    )

@tool(args_schema=BuscarPedidosInput)
def buscar_pedidos(cliente_id: int, limit: int = 5) -> str:
    """
    Busca los pedidos de un cliente específico.
    
    Cuándo usar:
    - Cuando el usuario pregunta sobre pedidos de un cliente
    - Para obtener el historial de compras
    - Para calcular totales de compras
    
    Retorna un resumen con:
    - Cantidad de pedidos
    - Total gastado
    - Detalle de productos
    """
    if cliente_id not in ORDENES:
        return f"❌ Cliente {cliente_id} no encontrado en la base de datos."
    
    pedidos = ORDENES[cliente_id][:limit]
    total = sum(p["precio"] * p["cantidad"] for p in pedidos)
    
    respuesta = f"📦 Pedidos para el cliente {cliente_id}:\n\n"
    respuesta += f"📊 Total de pedidos: {len(pedidos)}\n"
    respuesta += f"💰 Total gastado: ${total:,.0f}\n\n"
    respuesta += "📋 Detalles:\n"
    
    for p in pedidos:
        subtotal = p["precio"] * p["cantidad"]
        respuesta += f"  • {p['producto']} x {p['cantidad']} = ${subtotal:,.0f} ({p['fecha']})\n"
    
    return respuesta

class DescuentoInput(BaseModel):
    total: float = Field(
        description="Monto total a calcular descuento",
        gt=0
    )
    tipo_cliente: str = Field(
        default="regular",
        description="Tipo de cliente: 'regular', 'vip', 'premium'"
    )

@tool(args_schema=DescuentoInput)
def calcular_descuento(total: float, tipo_cliente: str = "regular") -> str:
    """
    Calcula el descuento aplicable según el monto y tipo de cliente.
    
    Reglas:
    - Regular: 0% (sin descuento)
    - VIP: 10% de descuento
    - Premium: 15% de descuento
    
    Además, si el total es mayor a $10,000, descuento adicional del 5%.
    """
    tipo_cliente = tipo_cliente.lower()
    if tipo_cliente not in ["regular", "vip", "premium"]:
        return f"❌ Tipo de cliente '{tipo_cliente}' no válido. Usá 'regular', 'vip' o 'premium'."
    
    descuentos = {"regular": 0.0, "vip": 0.10, "premium": 0.15}
    descuento_base = descuentos[tipo_cliente]
    
    descuento_adicional = 0.05 if total > 10000 else 0.0
    descuento_total = descuento_base + descuento_adicional
    
    monto_descuento = total * descuento_total
    total_final = total - monto_descuento
    
    return (
        f"💳 Cálculo de descuento:\n"
        f"  • Total base: ${total:,.0f}\n"
        f"  • Tipo cliente: {tipo_cliente.upper()}\n"
        f"  • Descuento base: {descuento_base*100:.0f}%\n"
        f"  • Descuento adicional: {descuento_adicional*100:.0f}%\n"
        f"  • Total descuento: {descuento_total*100:.0f}%\n"
        f"  • Total final: ${total_final:,.0f}"
    )

tools = [buscar_pedidos, calcular_descuento]