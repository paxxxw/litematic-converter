import sys
import os
import argparse
import struct
import io
import tempfile
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
try:
    from litemapy import Schematic, Region
    import nbtlib
    from PIL import Image, ImageDraw
except ImportError as e:
    print(
        f'Error: Missing library. Install with: pip install litemapy nbtlib Pillow'
        )
    sys.exit(1)
MAGIC_NUMBER = 182827830
CURRENT_VERSION = 1
DATA_VERSION = 4189
DEBUG = False

def _debug_banner_alignment(tile_entities_local, positions, palette):
    idx_to_state = {idx: state for state, idx in palette.items()}
    banner_block_coords = [coord for coord, idx in positions.items() if 
        'banner' in idx_to_state.get(idx, '').lower()]
    banner_entity_coords = [(int(te.get('x')), int(te.get('y')), int(te.get
        ('z'))) for te in tile_entities_local if te.get('id') ==
        'minecraft:banner']
    print('\n[DEBUG] ---- Banner alignment diagnostics ----')
    print(f'Blocks:  {len(banner_block_coords)} banner blocks')
    print(f'Entities: {len(banner_entity_coords)} banner entities')
    block_set = set(banner_block_coords)
    entity_set = set(banner_entity_coords)
    matches = block_set & entity_set
    print(f'Match count: {len(matches)}')
    if matches:
        print(f'  First 5 matches: {list(matches)[:5]}')
    print(f'Block-only (first 5): {list(block_set - entity_set)[:5]}')
    print(f'Entity-only (first 5): {list(entity_set - block_set)[:5]}')
    print('[DEBUG] -------------------------------------\n')

def create_header_nbt(litematic, block_count, contains_air):
    name = getattr(litematic, 'name', None) or 'Converted Blueprint'
    author = getattr(litematic, 'author', None) or 'Unknown'
    return nbtlib.Compound({'Version': nbtlib.Long(CURRENT_VERSION), 'Name':
        nbtlib.String(name), 'Author': nbtlib.String(author), 'Tags':
        nbtlib.List[nbtlib.String]([nbtlib.String('converted')]),
        'ThumbnailYaw': nbtlib.Float(135.0), 'ThumbnailPitch': nbtlib.Float
        (30.0), 'LockedThumbnail': nbtlib.Byte(0), 'BlockCount': nbtlib.Int
        (block_count), 'ContainsAir': nbtlib.Byte(1 if contains_air else 0)})

def create_thumbnail(positions, palette, dimensions, width=96, height=96):
    build_width, build_height, build_length = dimensions
    if not positions:
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 60, 76, 80], fill=(139, 69, 19, 255))
        draw.rectangle([25, 40, 71, 60], fill=(128, 128, 128, 255))
        draw.polygon([(20, 40), (48, 20), (76, 40)], fill=(165, 42, 42, 255))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    render_width, render_height = width * 2, height * 2
    img = Image.new('RGBA', (render_width, render_height), (0, 0, 0, 0))
    yaw = math.radians(135.0)
    pitch = math.radians(30.0)
    cos_pitch = math.cos(pitch)
    sin_pitch = math.sin(pitch)
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    cam_x = cos_pitch * cos_yaw
    cam_y = sin_pitch
    cam_z = cos_pitch * sin_yaw
    right_x = -sin_yaw
    right_y = 0
    right_z = cos_yaw
    up_x = cos_yaw * sin_pitch
    up_y = -cos_pitch
    up_z = sin_yaw * sin_pitch
    center_x = build_width / 2
    center_y = build_height / 2
    center_z = build_length / 2
    max_dim = max(build_width, build_height, build_length)
    cam_distance = max_dim * 1.8
    cam_pos_x = center_x - cam_x * cam_distance
    cam_pos_y = center_y - cam_y * cam_distance
    cam_pos_z = center_z - cam_z * cam_distance
    faces_to_render = []
    for (bx, by, bz), palette_idx in positions.items():
        block_state = None
        for state, idx in palette.items():
            if idx == palette_idx:
                block_state = state
                break
        if not block_state:
            continue
        base_color = get_block_color(block_state)
        faces = []
        face_directions = [(0, 1, 0, 'top'), (0, -1, 0, 'bottom'), (1, 0, 0,
            'east'), (-1, 0, 0, 'west'), (0, 0, 1, 'south'), (0, 0, -1,
            'north')]
        for dx, dy, dz, face_name in face_directions:
            neighbor_pos = bx + dx, by + dy, bz + dz
            if neighbor_pos not in positions:
                faces.append((face_name, dx, dy, dz))
        for face_name, nx, ny, nz in faces:
            minecraft_shaded_color = get_face_color(base_color, face_name)
            face_vertices = get_face_vertices(bx, by, bz, face_name)
            face_center_x = sum(v[0] for v in face_vertices) / 4
            face_center_y = sum(v[1] for v in face_vertices) / 4
            face_center_z = sum(v[2] for v in face_vertices) / 4
            rel_x = face_center_x - cam_pos_x
            rel_y = face_center_y - cam_pos_y
            rel_z = face_center_z - cam_pos_z
            depth = rel_x * cam_x + rel_y * cam_y + rel_z * cam_z
            faces_to_render.append((depth, face_vertices,
                minecraft_shaded_color, face_name, nx, ny, nz))
    faces_to_render.sort(key=lambda x: x[0], reverse=True)
    projected_faces = []
    all_screen_points = []
    for depth, vertices, base_color, face_name, nx, ny, nz in faces_to_render:
        screen_vertices = []
        for vx, vy, vz in vertices:
            rel_x = vx - cam_pos_x
            rel_y = vy - cam_pos_y
            rel_z = vz - cam_pos_z
            screen_x = rel_x * right_x + rel_y * right_y + rel_z * right_z
            screen_y = rel_x * up_x + rel_y * up_y + rel_z * up_z
            screen_y = -screen_y
            screen_vertices.append((screen_x, screen_y))
            all_screen_points.append((screen_x, screen_y))
        light_intensity = calculate_lighting(nx, ny, nz)
        final_color = apply_lighting(base_color, light_intensity)
        projected_faces.append((screen_vertices, final_color))
    if not all_screen_points:
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    min_x = min(p[0] for p in all_screen_points)
    max_x = max(p[0] for p in all_screen_points)
    min_y = min(p[1] for p in all_screen_points)
    max_y = max(p[1] for p in all_screen_points)
    screen_width = max_x - min_x
    screen_height = max_y - min_y
    if screen_width <= 0 or screen_height <= 0:
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    scale_x = render_width / screen_width
    scale_y = render_height / screen_height
    scale = min(scale_x, scale_y) * 0.95
    center_offset_x = render_width / 2 - (min_x + max_x) / 2 * scale
    center_offset_y = render_height / 2 - (min_y + max_y) / 2 * scale
    draw = ImageDraw.Draw(img)
    for screen_vertices, color in projected_faces:
        pixel_vertices = []
        for sx, sy in screen_vertices:
            px = int(sx * scale + center_offset_x)
            py = int(sy * scale + center_offset_y)
            pixel_vertices.append((px, py))
        if len(pixel_vertices) >= 3:
            draw.polygon(pixel_vertices, fill=color, outline=None)
    for screen_vertices, color in projected_faces:
        pixel_vertices = []
        for sx, sy in screen_vertices:
            px = int(sx * scale + center_offset_x)
            py = int(sy * scale + center_offset_y)
            pixel_vertices.append((px, py))
        if len(pixel_vertices) >= 3:
            edge_brightness = 8
            edge_color = tuple(min(255, c + edge_brightness) for c in color[:3]
                ) + (255,)
            draw.polygon(pixel_vertices, outline=edge_color)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True, compress_level=6)
    return buffer.getvalue()


def get_face_vertices(x, y, z, face_name):
    if face_name == 'top':
        return [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x,
            y + 1, z + 1)]
    elif face_name == 'bottom':
        return [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z), (x, y, z)]
    elif face_name == 'north':
        return [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]
    elif face_name == 'south':
        return [(x + 1, y, z + 1), (x, y, z + 1), (x, y + 1, z + 1), (x + 1,
            y + 1, z + 1)]
    elif face_name == 'west':
        return [(x, y, z + 1), (x, y, z), (x, y + 1, z), (x, y + 1, z + 1)]
    elif face_name == 'east':
        return [(x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x +
            1, y + 1, z)]
    return []


def get_face_color(base_color, face_name):
    r, g, b = base_color
    if face_name == 'top':
        brightness = 1.0
    elif face_name == 'bottom':
        brightness = 0.85
    elif face_name in ['north', 'south']:
        brightness = 0.95
    else:
        brightness = 0.9
    return int(r * brightness), int(g * brightness), int(b * brightness), 255


def calculate_lighting(nx, ny, nz):
    sun_x = 0.2
    sun_y = 0.8
    sun_z = 0.3
    length = math.sqrt(sun_x * sun_x + sun_y * sun_y + sun_z * sun_z)
    sun_x /= length
    sun_y /= length
    sun_z /= length
    dot = nx * sun_x + ny * sun_y + nz * sun_z
    return max(0.9, min(1.0, 0.95 + 0.05 * dot))


def apply_lighting(color, intensity):
    r, g, b = color[:3]
    return int(r * intensity), int(g * intensity), int(b * intensity), 255


def get_block_color(block_state):
    if '[' in block_state:
        block_name = block_state.split('[')[0]
    else:
        block_name = block_state
    if ':' in block_name:
        block_name = block_name.split(':')[1]
    if 'campfire' in block_name:
        return 139, 69, 19
    elif 'sea_pickle' in block_name:
        return 100, 200, 100
    elif 'candle' in block_name:
        return 255, 245, 200
    elif 'lantern' in block_name:
        if 'soul' in block_name:
            return 100, 150, 200
        else:
            return 255, 200, 100
    if any(wood in block_name for wood in ['oak', 'birch', 'spruce',
        'jungle', 'acacia', 'dark_oak', 'mangrove', 'cherry', 'bamboo']):
        wood_colors = {'oak': (160, 130, 75), 'birch': (192, 175, 121),
            'spruce': (114, 84, 48), 'jungle': (160, 115, 81), 'acacia': (
            186, 99, 56), 'dark_oak': (66, 43, 20), 'mangrove': (116, 62, 
            47), 'cherry': (210, 125, 140), 'bamboo': (195, 180, 90)}
        for wood_type, color in wood_colors.items():
            if wood_type in block_name:
                return color
        return 160, 130, 75
    if any(stone in block_name for stone in ['stone', 'granite', 'diorite',
        'andesite', 'cobble', 'brick']):
        if 'granite' in block_name:
            return 156, 105, 79
        elif 'diorite' in block_name:
            return 183, 183, 183
        elif 'andesite' in block_name:
            return 132, 134, 132
        elif 'cobble' in block_name:
            return 127, 127, 127
        elif 'brick' in block_name:
            return 150, 97, 83
        else:
            return 125, 125, 125
    if 'deepslate' in block_name:
        return 100, 100, 100
    if 'blackstone' in block_name:
        return 50, 50, 60
    if any(nether in block_name for nether in ['nether', 'crimson', 'warped']):
        if 'crimson' in block_name:
            return 180, 50, 50
        elif 'warped' in block_name:
            return 50, 180, 150
        elif 'nether_brick' in block_name:
            return 100, 50, 50
        else:
            return 120, 60, 60
    if any(earth in block_name for earth in ['dirt', 'grass', 'soil',
        'farmland', 'mycelium', 'podzol']):
        if 'grass' in block_name:
            return 95, 159, 53
        elif 'mycelium' in block_name:
            return 111, 99, 105
        elif 'podzol' in block_name:
            return 131, 85, 50
        else:
            return 134, 96, 67
    if 'sand' in block_name:
        if 'red' in block_name:
            return 190, 102, 33
        else:
            return 237, 216, 161
    color_map = {'white': (249, 255, 254), 'orange': (249, 128, 29),
        'magenta': (199, 78, 189), 'light_blue': (58, 175, 217), 'yellow':
        (254, 216, 61), 'lime': (128, 199, 31), 'pink': (243, 139, 170),
        'gray': (71, 79, 82), 'light_gray': (157, 157, 151), 'cyan': (22, 
        156, 156), 'purple': (137, 50, 184), 'blue': (60, 68, 170), 'brown':
        (131, 84, 50), 'green': (94, 124, 22), 'red': (176, 46, 38),
        'black': (29, 29, 33)}
    for color_name, rgb in color_map.items():
        if color_name in block_name:
            return rgb
    if 'leaves' in block_name:
        return 48, 120, 48
    if 'log' in block_name or 'stem' in block_name:
        return 101, 76, 51
    if 'planks' in block_name:
        return 160, 130, 75
    if any(ore in block_name for ore in ['iron', 'gold', 'diamond',
        'emerald', 'coal', 'copper', 'redstone']):
        ore_colors = {'iron': (135, 135, 135), 'gold': (255, 215, 0),
            'diamond': (185, 242, 255), 'emerald': (80, 220, 120), 'coal':
            (55, 55, 55), 'copper': (180, 118, 90), 'redstone': (170, 11, 11)}
        for ore_type, color in ore_colors.items():
            if ore_type in block_name:
                return color
    if 'glass' in block_name:
        return 160, 160, 160
    if 'ice' in block_name:
        return 174, 217, 255
    if ('water' in block_name or 'kelp' in block_name or 'seagrass' in
        block_name):
        return 64, 164, 223
    if 'vine' in block_name or 'moss' in block_name:
        return 90, 150, 90
    if 'slab' in block_name:
        base_name = block_name.replace('_slab', '')
        return get_block_color(base_name)
    if 'stairs' in block_name:
        base_name = block_name.replace('_stairs', '')
        return get_block_color(base_name)
    if 'fence' in block_name:
        if 'nether_brick' in block_name:
            return 100, 50, 50
        base_name = block_name.replace('_fence_gate', '').replace('_fence', '')
        return get_block_color(base_name)
    if 'wall' in block_name and 'torch' not in block_name:
        base_name = block_name.replace('_wall', '')
        return get_block_color(base_name)
    if 'dark' in block_name:
        return 60, 60, 60
    elif 'light' in block_name:
        return 200, 200, 200
    return 128, 128, 128


def pack_data_array(data, palette_size):
    bits_per_block = max(4, (palette_size - 1).bit_length())
    blocks_per_long = 64 // bits_per_block
    num_longs = (4096 + blocks_per_long - 1) // blocks_per_long
    packed_data = [0] * num_longs
    for i, block_id in enumerate(data):
        long_index = i // blocks_per_long
        bit_offset = i % blocks_per_long * bits_per_block
        packed_data[long_index] |= block_id << bit_offset
    for i in range(len(packed_data)):
        if packed_data[i] >= 2 ** 63:
            packed_data[i] -= 2 ** 64
    return packed_data


def create_block_data_nbt(chunks, block_entities=None):
    block_regions = []
    for chunk in chunks:
        palette_list = []
        sorted_palette = sorted(chunk['palette'].items(), key=lambda x: x[1])
        for block_state, index in sorted_palette:
            if '[' in block_state and block_state.endswith(']'):
                name, props_str = block_state.split('[', 1)
                props_str = props_str[:-1]
                properties = nbtlib.Compound()
                if props_str:
                    for prop in props_str.split(','):
                        key, value = prop.split('=', 1)
                        properties[key] = nbtlib.String(value)
                palette_entry = nbtlib.Compound({'Name': nbtlib.String(name
                    ), 'Properties': properties})
            else:
                palette_entry = nbtlib.Compound({'Name': nbtlib.String(
                    block_state)})
            palette_list.append(palette_entry)
        data_array = pack_data_array(chunk['data'], len(palette_list))
        chunk_nbt = nbtlib.Compound({'X': nbtlib.Int(chunk['x']), 'Y':
            nbtlib.Int(chunk['y']), 'Z': nbtlib.Int(chunk['z']),
            'BlockStates': nbtlib.Compound({'palette': nbtlib.List[nbtlib.
            Compound](palette_list), 'data': nbtlib.LongArray(data_array)})})
        block_regions.append(chunk_nbt)
    if block_entities is None:
        block_entities = []
    return nbtlib.Compound({'DataVersion': nbtlib.Int(DATA_VERSION),
        'BlockRegion': nbtlib.List[nbtlib.Compound](block_regions),
        'BlockEntities': nbtlib.List[nbtlib.Compound](block_entities),
        'Entities': nbtlib.List[nbtlib.Compound]([])})

def get_block_state_string(block):
    try:
        if hasattr(block, 'properties'):
            props = block.properties
            if callable(props):
                props = props()
            if props:
                props_dict = dict(props)
            else:
                props_dict = {}
        else:
            props_dict = {}
    except Exception as e:
        props_dict = {}
    if props_dict:
        sorted_props = sorted(props_dict.items())
        prop_string = ','.join([f'{k}={v}' for k, v in sorted_props])
        return f'{block.id}[{prop_string}]'
    return block.id


def find_bounding_box(region):
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    non_air_count = 0
    for x in region.xrange():
        for y in region.yrange():
            for z in region.zrange():
                try:
                    block = region[x, y, z]
                    if block.id != 'minecraft:air':
                        min_x, max_x = min(min_x, x), max(max_x, x)
                        min_y, max_y = min(min_y, y), max(max_y, y)
                        min_z, max_z = min(min_z, z), max(max_z, z)
                        non_air_count += 1
                except:
                    continue
    if non_air_count == 0:
        return 0, 0, 0, 0, 0, 0, 0
    return min_x, max_x, min_y, max_y, min_z, max_z, non_air_count


def collect_blocks(region, bounds):
    min_x, max_x, min_y, max_y, min_z, max_z, _ = bounds
    palette = {}
    positions = {}
    palette_index = 0
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            for z in range(min_z, max_z + 1):
                try:
                    block = region[x, y, z]
                    if block.id == 'minecraft:air':
                        continue
                    block_state = get_block_state_string(block)
                    if block_state not in palette:
                        palette[block_state] = palette_index
                        palette_index += 1
                    local_pos = x - min_x, y - min_y, z - min_z
                    positions[local_pos] = palette[block_state]
                except:
                    continue
    return palette, positions


def extract_tile_entities(litematic_file, region, bounds):
    min_x, max_x, min_y, max_y, min_z, max_z, _ = bounds
    tile_entities = []
    try:
        data = nbtlib.load(litematic_file)
        regions = data.get('Regions', {})
        if regions:
            region_name = list(regions.keys())[0]
            region_data = regions[region_name]
            if 'TileEntities' in region_data:
                tile_entities = region_data['TileEntities']
            elif 'BlockEntities' in region_data:
                tile_entities = region_data['BlockEntities']
        print(f'Found {len(tile_entities)} tile entities in litematic file')
    except Exception as e:
        print(f'Warning: Failed to extract tile entities: {e}')
        return []
    if tile_entities:
        te_min_x = min(int(te.get('x', 0)) for te in tile_entities)
        te_max_x = max(int(te.get('x', 0)) for te in tile_entities)
        te_min_y = min(int(te.get('y', 0)) for te in tile_entities)
        te_max_y = max(int(te.get('y', 0)) for te in tile_entities)
        te_min_z = min(int(te.get('z', 0)) for te in tile_entities)
        te_max_z = max(int(te.get('z', 0)) for te in tile_entities)
        print(
            f'Tile entity bounds: ({te_min_x}, {te_min_y}, {te_min_z}) to ({te_max_x}, {te_max_y}, {te_max_z})'
            )
        print(
            f'Block bounds: ({min_x}, {min_y}, {min_z}) to ({max_x}, {max_y}, {max_z})'
            )
        combined_min_x = min(min_x, te_min_x)
        combined_max_x = max(max_x, te_max_x)
        combined_min_y = min(min_y, te_min_y)
        combined_max_y = max(max_y, te_max_y)
        combined_min_z = min(min_z, te_min_z)
        combined_max_z = max(max_z, te_max_z)
        print(
            f'Combined bounds: ({combined_min_x}, {combined_min_y}, {combined_min_z}) to ({combined_max_x}, {combined_max_y}, {combined_max_z})'
            )
    else:
        combined_min_x, combined_max_x = min_x, max_x
        combined_min_y, combined_max_y = min_y, max_y
        combined_min_z, combined_max_z = min_z, max_z
    block_entities = []
    for tile_entity in tile_entities:
        try:
            orig_x = int(tile_entity.get('x', 0))
            orig_y = int(tile_entity.get('y', 0))
            orig_z = int(tile_entity.get('z', 0))
            facing = tile_entity.get('Facing', tile_entity.get('facing',
                'south'))
            if facing == 'east':
                orig_x -= 1
            elif facing == 'west':
                orig_x += 1
            elif facing == 'north':
                orig_z += 1
            elif facing == 'south':
                orig_z -= 1
            local_x = orig_x - combined_min_x
            local_y = orig_y - combined_min_y
            local_z = orig_z - combined_min_z
            block_entity_nbt = nbtlib.Compound({'x': nbtlib.Int(local_x),
                'y': nbtlib.Int(local_y), 'z': nbtlib.Int(local_z), 'id':
                nbtlib.String(str(tile_entity.get('id', '')))})
            for key, value in tile_entity.items():
                if key not in ['x', 'y', 'z', 'id']:
                    converted_value = convert_nbt_value(value)
                    if converted_value is not None:
                        block_entity_nbt[key] = converted_value
            block_entities.append(block_entity_nbt)
        except Exception as e:
            print(f'Warning: Failed to process tile entity: {e}')
            continue
    return block_entities, (combined_min_x, combined_max_x, combined_min_y,
        combined_max_y, combined_min_z, combined_max_z)

def convert_nbt_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return nbtlib.String(value)
    elif isinstance(value, int):
        return nbtlib.Int(value)
    elif isinstance(value, float):
        return nbtlib.Float(value)
    elif isinstance(value, bool):
        return nbtlib.Byte(1 if value else 0)
    elif isinstance(value, list):
        if not value:
            return nbtlib.List([])
        if isinstance(value[0], dict):
            compound_list = []
            for item in value:
                compound = nbtlib.Compound()
                for k, v in item.items():
                    converted = convert_nbt_value(v)
                    if converted is not None:
                        compound[k] = converted
                compound_list.append(compound)
            return nbtlib.List[nbtlib.Compound](compound_list)
        else:
            converted_list = []
            for item in value:
                converted = convert_nbt_value(item)
                if converted is not None:
                    converted_list.append(converted)
            return nbtlib.List(converted_list)
    elif isinstance(value, dict):
        compound = nbtlib.Compound()
        for k, v in value.items():
            converted = convert_nbt_value(v)
            if converted is not None:
                compound[k] = converted
        return compound
    else:
        try:
            return nbtlib.String(str(value))
        except:
            return None


def create_chunks(palette, positions, dimensions):
    width, height, length = dimensions
    chunk_min_x = 0 // 16
    chunk_max_x = (width - 1) // 16
    chunk_min_y = 0 // 16
    chunk_max_y = (height - 1) // 16
    chunk_min_z = 0 // 16
    chunk_max_z = (length - 1) // 16
    chunk_dict = {}
    for (local_x, local_y, local_z), palette_idx in positions.items():
        world_x, world_y, world_z = local_x, local_y, local_z
        chunk_x = world_x // 16
        chunk_y = world_y // 16
        chunk_z = world_z // 16
        local_chunk_x = world_x % 16
        local_chunk_y = world_y % 16
        local_chunk_z = world_z % 16
        chunk_key = chunk_x, chunk_y, chunk_z
        if chunk_key not in chunk_dict:
            chunk_dict[chunk_key] = {'x': chunk_x, 'y': chunk_y, 'z':
                chunk_z, 'palette': {'minecraft:structure_void': 0}, 'data':
                [0] * 4096, 'palette_index': 1}
        chunk = chunk_dict[chunk_key]
        block_state = None
        for state, idx in palette.items():
            if idx == palette_idx:
                block_state = state
                break
        if not block_state:
            continue
        if block_state not in chunk['palette']:
            chunk['palette'][block_state] = chunk['palette_index']
            chunk['palette_index'] += 1
        data_index = local_chunk_y * 256 + local_chunk_z * 16 + local_chunk_x
        chunk['data'][data_index] = chunk['palette'][block_state]
    return list(chunk_dict.values())


def write_bp_file(output_path, header_nbt, thumbnail_data, block_data_nbt):
    with open(output_path, 'wb') as f:
        f.write(struct.pack('>I', MAGIC_NUMBER))
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name
        header_file = nbtlib.File(header_nbt)
        header_file.save(temp_path, gzipped=False)
        with open(temp_path, 'rb') as temp:
            header_data = temp.read()
        os.unlink(temp_path)
        f.write(struct.pack('>I', len(header_data)))
        f.write(header_data)
        f.write(struct.pack('>I', len(thumbnail_data)))
        f.write(thumbnail_data)
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name
        block_file = nbtlib.File(block_data_nbt)
        block_file.save(temp_path, gzipped=True)
        with open(temp_path, 'rb') as temp:
            block_data_compressed = temp.read()
        os.unlink(temp_path)
        f.write(struct.pack('>I', len(block_data_compressed)))
        f.write(block_data_compressed)

def convert_litematic_to_bp(litematic_path, output_path):
    print(f'Loading: {litematic_path}')
    try:
        litematic = Schematic.load(litematic_path)
    except Exception as e:
        print(f'Error loading file: {e}')
        return False
    base_name = Path(litematic_path).stem
    litematic.name = base_name
    print(f'Name (from filename): {litematic.name}')
    print(f'Author: {litematic.author}')
    regions = litematic.regions
    region_name = list(regions.keys())[0]
    region = regions[region_name]
    print(f'Original size: {region.width}x{region.height}x{region.length}')
    bounds = find_bounding_box(region)
    min_x, max_x, min_y, max_y, min_z, max_z, non_air_count = bounds
    if non_air_count == 0:
        print('No blocks found')
        return False
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    length = max_z - min_z + 1
    print(f'Optimized size: {width}x{height}x{length}')
    print(f'Blocks: {non_air_count}')
    palette, positions = collect_blocks(region, bounds)
    print(f'Unique block types: {len(palette)}')
    tile_entities, combined_bounds = extract_tile_entities(litematic_path,
        region, bounds)
    print(f'Tile entities: {len(tile_entities)}')
    if tile_entities:
        (combined_min_x, combined_max_x, combined_min_y, combined_max_y,
            combined_min_z, combined_max_z) = combined_bounds
        width = combined_max_x - combined_min_x + 1
        height = combined_max_y - combined_min_y + 1
        length = combined_max_z - combined_min_z + 1
        print(f'Updated size with tile entities: {width}x{height}x{length}')
        palette, positions = collect_blocks(region, combined_bounds + (
            non_air_count,))
        if tile_entities:
            try:
                idx_to_state = {idx: state for state, idx in palette.items()}
                banner_block_coords = [coord for coord, idx in positions.
                    items() if 'banner' in idx_to_state.get(idx, '').lower()]
                if banner_block_coords:
                    block_min = min(c[0] for c in banner_block_coords), min(
                        c[1] for c in banner_block_coords), min(c[2] for c in
                        banner_block_coords)
                    banner_entity_coords = [(int(te['x']), int(te['y']),
                        int(te['z'])) for te in tile_entities if te.get(
                        'id') == 'minecraft:banner']
                    entity_min = min(c[0] for c in banner_entity_coords), min(
                        c[1] for c in banner_entity_coords), min(c[2] for c in
                        banner_entity_coords)
                    dx, dy, dz = (entity_min[i] - block_min[i] for i in
                        range(3))
                    if dx or dy or dz:
                        for te in tile_entities:
                            te['x'] = nbtlib.Int(int(te['x']) - dx)
                            te['y'] = nbtlib.Int(int(te['y']) - dy)
                            te['z'] = nbtlib.Int(int(te['z']) - dz)
                        if DEBUG:
                            print(
                                f'[DEBUG] Shifted tile-entity coords by (dx={-dx}, dy={-dy}, dz={-dz}) for banner alignment'
                                )
            except Exception as shift_exc:
                if DEBUG:
                    print(f'[DEBUG] Alignment shift failed: {shift_exc}')
        print(f'Unique block types (updated): {len(palette)}')
    chunks = create_chunks(palette, positions, (width, height, length))
    print(f'Chunks: {len(chunks)}')
    if not chunks:
        chunks = [{'x': 0, 'y': 0, 'z': 0, 'palette': {'minecraft:air': 0},
            'data': [0] * 4096}]
    header_nbt = create_header_nbt(litematic, non_air_count, False)
    thumbnail_data = create_thumbnail(positions, palette, (width, height,
        length))
    block_data_nbt = create_block_data_nbt(chunks, tile_entities)
    if DEBUG:
        try:
            _debug_banner_alignment(tile_entities, positions, palette)
        except Exception as dbg_exc:
            if DEBUG:
                print(f'[DEBUG] Banner alignment check failed: {dbg_exc}')
    print(f'Writing: {output_path}')
    try:
        write_bp_file(output_path, header_nbt, thumbnail_data, block_data_nbt)
        print('✓ Conversion completed')
        return True
    except Exception as e:
        print(f'Error writing file: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(description=
        'Convert .litematic files to Axiom .bp files')
    parser.add_argument('input_file', help='Input .litematic file')
    parser.add_argument('output_file', nargs='?', help=
        'Output .bp file (optional)')
    args = parser.parse_args()
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found")
        return
    output_file = (args.output_file or
        f'{os.path.splitext(args.input_file)[0]}.bp')
    success = convert_litematic_to_bp(args.input_file, output_file)
    if not success:
        sys.exit(1)
if __name__ == '__main__':
    main()