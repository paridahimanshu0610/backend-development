from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional
from random import randrange
import psycopg2 as pg
from psycopg2.extras import RealDictCursor

app = FastAPI()

try:
    conn = pg.connect(
        host = "127.0.0.1",
        database = "fastapi",
        user = "postgres",
        password = "test",
        cursor_factory = RealDictCursor
    )
    cursor = conn.cursor()
    print("Successfully established connection with the database.")
except Exception as error:
    print("Connection failed due to this error: ", error)

all_posts = [
    {"id": 1, "title": "dummy post 1", "content": "dummy content 1"}, 
    {"id": 2, "title": "dummy post 2", "content": "dummy content 2"}
    ]

@app.get("/")
def root():
    return {"message":"home page!!"}

# Pydantic datamodel
class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    # rating: Optional[int] = None

class UpdatePost(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published: bool = True
    # rating: Optional[int] = None 


def find_post_by_query(id=None):
    if id==None:
        return all_posts
    
    for post in all_posts:
        if post['id'] == id:
            return post
        
def find_post_by_query(id=None):
    base_query = "select * from post"
    
    if id is None:
        filter_query, filter_vals = "", ()
    else:
        filter_query, filter_vals = " where id=%s", (id,)
    
    cursor.execute(base_query + filter_query, filter_vals)
    return cursor.fetchall()
        
def create_post_by_query(post:dict):
    query = """insert into post (title, content, published) values (%s, %s, %s) returning *"""
    try:
        cursor.execute(query, (post.title, post.content, post.published))
        conn.commit()
        return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print("Something went wrong while creating post: ", e)
        # If `create_post_by_query` catches an exception and doesn’t re-raise, `temp` in `create_post` would be None, and the endpoint would return a fake 201 success
        raise # <- re-raise the exception

@app.post("/posts", status_code = status.HTTP_201_CREATED)
def create_post(post:Post): # def create_post(post:dict = Body(...))

    # Implementation 1: When posts are stored in all_posts 
    # temp = post.model_dump()
    # temp['id'] = randrange(1, 10**6)
    # all_posts.append(temp)
    # return {"message": temp}

    # Implemenation 2: When posts are stored in dv
    try:
        temp = create_post_by_query(post)
        return {"message": temp}
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))

@app.get("/posts")
def get_all_posts(response: Response):
    res = find_post_by_query(id=None)

    # if not res:
    #     response.status_code = status.HTTP_404_NOT_FOUND
    #     return {"detail": "No post was found."}

    if not res:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "No post was found."
        )

    return res 

@app.get("/posts/{id}")
def get_one_post(id:int, response: Response):
    res = find_post_by_query(id=id)

    # Method 1: Using response.status
    # if not res:
    #     response.status_code = status.HTTP_404_NOT_FOUND
    #     return {"detail" : f"post with id: {id} was not found."}

    # Method 2: Using HTTPException
    if not res:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"post with id: {id} was not found."
        )

    return res

def find_post_pos(id):
    for i, post in enumerate(all_posts):
        if post["id"] == id:
            return i    

@app.patch("/posts/{id}", status_code = status.HTTP_200_OK)
def update_post(id: int, post: UpdatePost):
    # Directly using post.model_dump() will include the unset parameters as well. They will be set to their default values.
    # Using PATCH instead of PUT does not automatically make updates partial. Your code logic decides that, not the HTTP method.
    # Get only fields sent by the client
    update_data = post.model_dump(exclude_unset=True)
    
    # Implementation 1: Merge with existing post list
    # post_idx = find_post_pos(id)
    # if post_idx == None:
    #     raise HTTPException(
    #         status_code = status.HTTP_404_NOT_FOUND,
    #         detail = f"Post with id: {id} does not exist"
    #     )
    # all_posts[post_idx].update(update_data)

    # Implementation 2: Updating the post in database
    update_query = ", ".join(f"{key} = '{val}'" for key, val in update_data.items())
    try:
        print(update_query)
        cursor.execute("update post set " + update_query + " where id=%s returning *", (id, ))
        if not cursor.rowcount:
            raise ValueError(f"Post with {id} was not found.")
        updated_post = cursor.fetchone()
        conn.commit()
        # With Response, we should never send body parameter value. Because `response.body` expects "bytes", not a Python object like dictionary, list, etc.
        return {"data" : updated_post}
    
    except ValueError as e:
        conn.rollback()
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = str(e)
            )
    
    except Exception as e:
        print(e)
        conn.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "An internal issue was encountered while deleting the post."
        )


def delete_post_by_query(id: int):
    try:
        cursor.execute("DELETE FROM post WHERE id = %s", (id,))

        if cursor.rowcount == 0:
            raise ValueError(f"Post with id {id} not found")

        conn.commit()

    except ValueError:
        # Business error → rollback and propagate
        conn.rollback()
        raise

    except Exception as e:
        # System / DB error
        conn.rollback()
        raise RuntimeError("Database error while deleting post") from e


@app.delete("/posts/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_post(id:int):
    # Implementation 1: When post is stored in a list
    # post_idx = find_post_pos(id)
    # if post_idx == None:
    #     raise HTTPException(
    #         status_code = status.HTTP_404_NOT_FOUND,
    #         detail = f"Post with id: {id} does not exist"
    #     ) 
    # all_posts.pop(post_idx)
    # This is not required as the default status is already set to 204 and also, since status is 204, no content should be returned
    # return Response(status_code = status.HTTP_204_NO_CONTENT)


    # Implementation 2: When post is stored in the database
    try:
        delete_post_by_query(id)
    except ValueError as e:
        # Not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while deleting the post"
        )