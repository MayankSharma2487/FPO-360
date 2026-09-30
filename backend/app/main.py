from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.organizations import router as organization_router
from app.api.organization_settings import router as organization_settings_router
from app.api.roles import router as role_router
from app.api.users import router as user_router
from app.api.dashboard import router as dashboard_router
from app.api.villages import router as villages_router  # NEW
from app.api.masters import router as masters_router
from app.api.farmers import router as farmers_router
from app.api.shareholders import router as shareholders_router
from app.api.crop_masters import router as crop_masters_router
from app.api.farmer_crops import router as farmer_crops_router
from app.api.procurement import router as procurement_router
# Add to imports
from app.routers import payment
from app.api.inventory import router as inventory_router


app = FastAPI(
    title="FPO360 ERP",
    version="1.0.0",
    description="Backend API for FPO360 - Farmer Producer Organization ERP"
)

app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(organization_settings_router)
app.include_router(role_router)
app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(villages_router)  # NEW
app.include_router(masters_router)  
app.include_router(farmers_router)
app.include_router(shareholders_router)
app.include_router(crop_masters_router)
app.include_router(farmer_crops_router)
app.include_router(procurement_router)
app.include_router(payment.router)
app.include_router(inventory_router)

@app.get("/")
def home():
    return {
        "message": "FPO360 ERP API Running"
    }