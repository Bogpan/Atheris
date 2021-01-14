import asyncpg
import asyncio


async def main():
    conn = await asyncpg.connect("postgres://postgres:Dyn0SucksLOL,,RaptorAndPartsBoTBetter904@localhost:5432/Atheris")

    # await conn.execute("DELETE FROM guild")

    await conn.execute("SELECT setval('warns_warn_id_seq', 1)")

    await conn.close()



loop = asyncio.get_event_loop()
loop.run_until_complete(main())