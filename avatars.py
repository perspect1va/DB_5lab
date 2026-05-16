import asyncio
import base64
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie

# ЗАДАНИЕ 3

class Avatar(Document):
    username: str
    image_base64: str
    image_type: str = "image/jpeg"

    class Settings:
        name = "Avatars"

def image_to_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["AVATARS"]
    await init_beanie(database=db, document_models=[Avatar])
    await Avatar.find_all().delete()
    try:
        base64_string = image_to_base64("test.jpg")
        avatar = Avatar(
            username="Админ",
            image_base64=base64_string
        )
        await avatar.insert()
        print("Аватар сохранен в базу AVATARS")
        print(f"  Имя пользователя: {avatar.username}")
        print(f"  Тип: {avatar.image_type}")
        print(f"  Размер base64: {len(base64_string)} символов")
        saved = await Avatar.find_one({"username": "Админ"})
        if saved:
            print("аватар найден в базе")
    except FileNotFoundError:
        print("Ошибка: не найден файл test.jpg")
        print("Положите картинку test.jpg в папку и запустите снова")

if __name__ == "__main__":
    asyncio.run(main())