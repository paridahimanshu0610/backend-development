from datetime import datetime
from typing import Annotated, Literal, Optional, Union

import mysql.connector
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.concurrency import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from fastapi.params import Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World gj"}

# Here, q is an optional query parameter, which can be: 
# a string if provided in the request (e.g. /items/1?q=hello)
# None if not provided (e.g. /items/1).
# Union is not a data type — it’s a type hint that tells Python tools “this variable can be one of several types.”
# Instead of Union[str, None] we could have written: q: Optional[str] = None 
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

# Retrieving request body using Body()
@app.post("/create/")
def create_post(payload : dict = Body(...)):
    return {"title":payload.get("title", None), "content":payload.get("content", None), "time":payload.get("time", None)}


# Creating a pydantic data model for request body
class CreateItem(BaseModel):
    title: str
    post_content: str
    time: datetime | None = None

@app.post("/create/{path_id}")
def new_create(
    path_id: int,
    payload: Optional[CreateItem] = None,
    q1: str | int | None = None,
    q2: Optional[bool] = None
):
    return {
        "path_id": path_id,
        "q1": q1,
        "q2": q2,
        **(payload.model_dump() if payload else {})
    }

# Creating a pydantic data model for query parameters
class FilterParams(BaseModel): 
    limit: int = Field(100, gt=0, le=100) # default=100, must be >0 and <=100
    offset: int = Field(0, ge=0) # default=0, must be >=0
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/new_query/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

# Handling response status code
# @app.get("/posts/{id}")
# def get_post(id:int, response: Response):
#     my_posts = {1: '1st post', 2: '2nd post', 3: '3rd post'}
#     post = my_posts.get(id, None)

#     if not post:
#         response.status_code = status.HTTP_404_NOT_FOUND # We could also write response.status_code = 404
#         return {"message": f"post with id:{id} not found."}

#     return {"target_post": post}

# Error handling and setting default status code
my_posts = {1: '1st post', 2: '2nd post', 3: '3rd post'}
@app.get("/posts/{id}", status_code=status.HTTP_201_CREATED)
def get_post(id:int):
    post = my_posts.get(id, None)

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"post with id:{id} not found.")

    return {"target_post": post}

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id:int):
    if id in my_posts:
        del my_posts[id]
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post with id:{id} not found.")
    
    # content will not be returned in the response becuase the status_code parameter in delete method i.e. @app.delete above has been set to 204
    return Response(content = "wow, I deleted it", status_code=status.HTTP_204_NO_CONTENT)

########################### API with SQL database connection ###########################
try:
    conn = mysql.connector.connect(
        host="127.0.0.1",      # force TCP (don’t use "localhost")
        port=3306,
        user="root",
        password="root",
        database="fastpi",
        connection_timeout=5,
        use_pure=True          # bypass C extension, force Python implementation
    )
    print("Connected:", conn.is_connected())
    mycursor = conn.cursor(dictionary = True) #dictionary = True
except Exception as e:
    print("Error:", e)

@app.get("/get_posts/", status_code=status.HTTP_200_OK)
def get_all_posts():
    try:
        mycursor.execute("SELECT * FROM post")
        result = mycursor.fetchall()
        print(type(result))
        print(result)
        return JSONResponse(content=jsonable_encoder({"posts": result}), status_code=status.HTTP_200_OK)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

class CreatePost(BaseModel):
    title: str
    content: str
    published: bool = True
    # date_created: datetime = Field(default_factory=datetime.now)

@app.post("/create_post/", status_code=status.HTTP_201_CREATED)
def create_post(post: CreatePost):
    sql = "INSERT INTO post (title, content, published) VALUES (%(param1)s, %(param2)s, %(param3)s)"
    values = {"param1":post.title, "param2":post.content, "param3":post.published}
    try:
        mycursor.execute(sql, values)
        conn.commit()
        response_data = {
            "message": "Post created successfully",
            "post_id": mycursor.lastrowid
        }
        return JSONResponse(content= jsonable_encoder(response_data), status_code=status.HTTP_201_CREATED)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database Error: {e}")
    
@app.get("/single_post/{id}", status_code = status.HTTP_200_OK)
def get_single_post(id: int):
    try:
        mycursor.execute("select * from post where id = %(id)s", {'id':str(id)})
        result = mycursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database Error: {e}")
    
    # Checking if result is None
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id:{id} not found.")
    
    return JSONResponse(content = jsonable_encoder(result), status_code = status.HTTP_200_OK)

@app.delete("/delete_post/{id}", status_code=status.HTTP_200_OK)
def delete_post(id: int):
    try:
        mycursor.execute("delete from post where id = %(id)s", {"id":str(id)})
        affected_rows = mycursor.rowcount
        print("affected_rows:", affected_rows)
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database Error: {e}")
    
    if affected_rows == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id:{id} not found.")
    
    return Response(content=f"Successfully deleted the post with id:{id}", status_code=status.HTTP_200_OK)