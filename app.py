import aiomysql
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()


class Task(BaseModel):
    id_get: int = Query(..., description='enter id for your task')
    description_get: str = Query(..., description='enter description for your task')


async def get_db_pool():
    return await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='root',
        password='password',
        db='db',
        minsize=5,
        maxsize=10
    )


async def execute_query(query: str, params=None):
    pool = await get_db_pool()
    try:
        async with pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, params)

                if query.strip().lower().startswith('select'):
                    return await cursor.fetchall()
                elif query.strip().lower().startswith(('insert', 'update', 'delete')):
                    await connection.commit()
                    return {'message': 'Query executed succesfully'}
    finally:
        pool.close()
        await pool.wait_closed()


async def create_database():
    await execute_query("""
    CREATE DATABASE IF NOT EXISTS db;
    """)


async def create_table():
    await execute_query("""
    CREATE TABLE IF NOT EXISTS data(
    id INT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(255),
    content TEXT
    );
    """)


@app.on_event('startup')
async def startup_event():
    await create_database()
    await create_table()


@app.post('/task_add/')
async def task_add(task: Task):
    try:
        await execute_query("""
        INSERT INTO data (id, description) VALUES (%s, %s)
        """,
                            (task.id_get, task.description_get)
                            )
    except:
        raise HTTPException(status_code=400, detail='Enter valid data')


@app.put('/task_edit/')
async def task_edit(task: Task):
    try:
        await execute_query("""
        UPDATE data 
        SET description = %s
        WHERE id = %s
        """,
                            (task.description_get, task.id_get)
                            )
    except:
        raise HTTPException(status_code=400, detail='Enter valid data')


@app.delete('/task_delete/')
async def task_delete(task: Task):
    try:
        await execute_query("""
        DELETE FROM data WHERE id = %s
        """,
                            (task.id_get,)
                            )
    except:
        raise HTTPException(status_code=400, detail='Enter valid data')


@app.get('/task_get_one/')
async def task_get_one(task: Task):
    try:
        response = await execute_query("""
        SELECT * FROM data WHERE id = %s
        """,
                            (task.id_get,)
                            )
        return{'response': response}
    except:
        raise HTTPException(status_code=400, detail='Enter valid data')


@app.get('/task_get_all/')
async def task_get_all():
    try:
        response = await execute_query("""
        SELECT * FROM data
        """)
        return {'response': response}
    except:
        raise HTTPException(status_code=400, detail='Enter valid data')
