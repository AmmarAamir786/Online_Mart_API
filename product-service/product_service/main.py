from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List
from fastapi import Depends, FastAPI, HTTPException
from product_service.models import Product, Product_Update
from sqlmodel import Session, select


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(lifespan=lifespan, title="Product Service", version='1.0.0')


@app.get('/')
async def root() -> Any:
    return {"message": "Welcome to products section"}

# @app.get('/products/', response_model=List[Product])
# async def get_all_products(session: Session = Depends(get_session)) -> List[Product]:
#     products = list(session.exec(select(Product)).all())
#     if products:
#         return products
#     else:
#         raise HTTPException(status_code=404, detail="No products found")


# @app.get('/products/{id}', response_model=Product)
# async def get_single_product(id: int, session: Session = Depends(get_session)) -> Product:
#     product = session.get(Product, id)
#     if product:
#         return product
#     else:
#         raise HTTPException(status_code=404, detail="Product not found")
    

# @app.put('/products/{id}', response_model=Product)
# async def edit_product(id: int, product: Product_Update, session: Session = Depends(get_session)) -> Product:
#     existing_product = session.get(Product, id)
#     if existing_product:
#         existing_product.name = product.name
#         existing_product.price = product.price
#         existing_product.quantity = product.quantity
#         session.add(existing_product)
#         session.commit()
#         session.refresh(existing_product)
#         return existing_product
#     else:
#         raise HTTPException(status_code=404, detail="Product not found")
    

# @app.delete('/products/{id}')
# async def delete_product(id: int, session: Session = Depends(get_session)) -> Any:
#     product = session.get(Product, id)
#     if product:
#         session.delete(product)
#         session.commit()
#         return {"message": "Product successfully deleted"}
#     else:
#         raise HTTPException(status_code=404, detail="Product not found")