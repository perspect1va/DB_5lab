import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie
from pydantic import BaseModel

# ЗАДАНИЕ 1

class Category(BaseModel):
    type: str
    description: str

class PCComponent(Document):
    production: str
    model: str
    price: float
    category: Category
    specs: dict

    class Settings:
        name = "PC_components"

# ЗАДАНИЕ 2

async def get_cheapest_and_expensive_build():
    print("\n1. Самая дешевая и дорогая сборка:")
    boards = await PCComponent.find({"category.type": "материнская плата"}).to_list()
    cpus = await PCComponent.find({"category.type": "процессор"}).to_list()
    builds = []
    for board in boards:
        for cpu in cpus:
            if board.specs.get("socket") == cpu.specs.get("socket"):
                builds.append({
                    "board": board,
                    "cpu": cpu,
                    "pair_price": board.price + cpu.price
                })
    if not builds:
        print("Не найдено совместимых сборок")
        return
    cheapest = min(builds, key=lambda x: x["pair_price"])
    expensive = max(builds, key=lambda x: x["pair_price"])
    cheap_rest = 0
    expensive_rest = 0
    for cat in ["ОЗУ", "ПЗУ", "видеокарта"]:
        items = await PCComponent.find({"category.type": cat}).sort("+price").to_list()
        if items:
            cheap_rest += items[0].price
            expensive_rest += items[-1].price
    print(f"Дешевая сборка: {cheapest['board'].production} {cheapest['board'].model} + {cheapest['cpu'].production} {cheapest['cpu'].model}")
    print(f"Цена: {cheapest['pair_price'] + cheap_rest} руб.")
    print(f"\nДорогая сборка: {expensive['board'].production} {expensive['board'].model} + {expensive['cpu'].production} {expensive['cpu'].model}")
    print(f"Цена: {expensive['pair_price'] + expensive_rest} руб.")

async def get_third_and_fifth_items():
    print("\n2. Третий и пятый товары из каждой категории:")
    categories = ["материнская плата", "процессор", "ОЗУ", "ПЗУ", "видеокарта"]
    for cat in categories:
        items = await PCComponent.find({"category.type": cat}).sort("+price").to_list()
        print(f"\n{cat}:")
        if len(items) >= 3:
            third = items[2]
            print(f"  3-й по цене: {third.production} {third.model} - {third.price} руб.")
        else:
            print(f"  3-й по цене: нет данных (всего {len(items)} товаров)")
        if len(items) >= 5:
            fifth = items[4]
            print(f"  5-й по цене: {fifth.production} {fifth.model} - {fifth.price} руб.")
        else:
            print(f"  5-й по цене: нет данных (всего {len(items)} товаров)")

async def get_am4_builds():
    print("\n3. Все сборки на сокете AM4:")
    am4_boards = await PCComponent.find({
        "category.type": "материнская плата",
        "specs.socket": "AM4"
    }).to_list()
    am4_cpus = await PCComponent.find({
        "category.type": "процессор",
        "specs.socket": "AM4"
    }).to_list()
    if not am4_boards or not am4_cpus:
        print("Нет компонентов под AM4")
        return
    print(f"Найдено материнских плат AM4: {len(am4_boards)}")
    print(f"Найдено процессоров AM4: {len(am4_cpus)}")
    print(f"Всего возможных сборок: {len(am4_boards) * len(am4_cpus)}\n")
    count = 0
    for board in am4_boards:
        for cpu in am4_cpus:
            count += 1
            print(f"{count}. {board.production} {board.model} ({board.price} руб.) + {cpu.production} {cpu.model} ({cpu.price} руб.) = {board.price + cpu.price} руб.")

async def fill_database():
    components_data = {
        "материнская плата": [
            {"specs": {"format": "ATX", "socket": "AM4"}, "price": 5000, "models": ["B550 Aorus", "B550 Tomahawk"]},
            {"specs": {"format": "mATX", "socket": "AM4"}, "price": 4000, "models": ["B550M Pro", "A520M-A"]},
            {"specs": {"format": "ATX", "socket": "LGA1700"}, "price": 6000, "models": ["Z690-A", "B760 Plus"]},
            {"specs": {"format": "Mini-ITX", "socket": "AM5"}, "price": 7000, "models": ["B650I Aorus", "ROG Strix B650E-I"]},
            {"specs": {"format": "ATX", "socket": "AM4"}, "price": 4500, "models": ["X570 Gaming Plus", "B550 Steel Legend"]},
            {"specs": {"format": "mATX", "socket": "LGA1700"}, "price": 5500, "models": ["B760M Mortar", "Z790M-Plus"]},
        ],
        "процессор": [
            {"specs": {"socket": "AM4", "frequency": "3.6 GHz"}, "price": 8000, "models": ["Ryzen 5 3600", "Ryzen 7 3700X"]},
            {"specs": {"socket": "AM4", "frequency": "4.2 GHz"}, "price": 12000, "models": ["Ryzen 5 5600X", "Ryzen 7 5800X"]},
            {"specs": {"socket": "LGA1700", "frequency": "3.8 GHz"}, "price": 10000, "models": ["i5-12400F", "i7-12700K"]},
            {"specs": {"socket": "AM5", "frequency": "4.5 GHz"}, "price": 20000, "models": ["Ryzen 7 7700X", "Ryzen 9 7900X"]},
            {"specs": {"socket": "AM4", "frequency": "3.4 GHz"}, "price": 6000, "models": ["Ryzen 3 3100", "Ryzen 5 2600"]},
            {"specs": {"socket": "LGA1700", "frequency": "4.0 GHz"}, "price": 15000, "models": ["i5-13600K", "i7-13700K"]},
        ],
        "ОЗУ": [
            {"specs": {"frequency": "3200 MHz", "volume": "16 GB"}, "price": 3000, "models": ["Fury Beast", "Vengeance LPX"]},
            {"specs": {"frequency": "3600 MHz", "volume": "32 GB"}, "price": 5000, "models": ["Trident Z", "Ballistix"]},
            {"specs": {"frequency": "2666 MHz", "volume": "8 GB"}, "price": 2000, "models": ["ValueRAM", "Basic DDR4"]},
            {"specs": {"frequency": "6000 MHz", "volume": "32 GB"}, "price": 8000, "models": ["Trident Z5", "Vengeance DDR5"]},
            {"specs": {"frequency": "4800 MHz", "volume": "16 GB"}, "price": 4000, "models": ["Crucial DDR5", "Kingston FURY"]},
            {"specs": {"frequency": "3200 MHz", "volume": "64 GB"}, "price": 7000, "models": ["Corsair Dominator", "G.Skill Ripjaws"]},
        ],
        "ПЗУ": [
            {"specs": {"formFactor": "M.2", "volume": "512 GB"}, "price": 3500, "models": ["980 Pro", "SN770"]},
            {"specs": {"formFactor": "M.2", "volume": "1 TB"}, "price": 5000, "models": ["990 Pro", "SN850X"]},
            {"specs": {"formFactor": "2.5\"", "volume": "256 GB"}, "price": 2000, "models": ["MX500", "Ultra 3D"]},
            {"specs": {"formFactor": "M.2", "volume": "2 TB"}, "price": 8000, "models": ["FireCuda 530", "WD Black SN850X"]},
            {"specs": {"formFactor": "3.5\"", "volume": "1 TB"}, "price": 2500, "models": ["BarraCuda", "WD Blue"]},
            {"specs": {"formFactor": "M.2", "volume": "4 TB"}, "price": 15000, "models": ["Sabrent Rocket", "Samsung 990 Pro"]},
        ],
        "видеокарта": [
            {"specs": {"ports": "HDMI, DP", "volume": "8 GB"}, "price": 15000, "models": ["RTX 3060", "RX 6600"]},
            {"specs": {"ports": "HDMI, 3xDP", "volume": "12 GB"}, "price": 25000, "models": ["RTX 4070", "RX 7700 XT"]},
            {"specs": {"ports": "2xHDMI, 2xDP", "volume": "16 GB"}, "price": 35000, "models": ["RTX 4080", "RX 7900 XT"]},
            {"specs": {"ports": "HDMI, DP, USB-C", "volume": "24 GB"}, "price": 50000, "models": ["RTX 4090", "RX 7900 XTX"]},
            {"specs": {"ports": "3xDP, HDMI", "volume": "6 GB"}, "price": 10000, "models": ["RTX 3050", "RX 6500 XT"]},
            {"specs": {"ports": "2xHDMI, DP", "volume": "10 GB"}, "price": 20000, "models": ["RTX 3080", "RX 6800"]},
        ]
    }
    
    vendors = ["Gigabyte", "MSI", "ASUS", "AMD", "Intel", "Kingston", "Corsair", "Samsung", "WD", "Palit", "Zotac", "Sapphire"]
    all_components = []
    
    for category, items in components_data.items():
        for item in items:
            for model in item["models"]:
                component = PCComponent(
                    production=vendors[len(all_components) % len(vendors)],
                    model=model,
                    price=item["price"],
                    category=Category(type=category, description=f"Качественный {category}"),
                    specs=item["specs"]
                )
                all_components.append(component)
    
    await PCComponent.insert_many(all_components)
    print(f"Добавлено {len(all_components)} компонентов в базу данных")

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["Catalog"]
    await init_beanie(database=db, document_models=[PCComponent])
    await PCComponent.find_all().delete()
    print("\nЗАДАНИЕ 1")
    await fill_database()
    print("\nЗАДАНИЕ 2")
    await get_cheapest_and_expensive_build()
    await get_third_and_fifth_items()
    await get_am4_builds()
    print("\nГотово")

if __name__ == "__main__":
    asyncio.run(main())