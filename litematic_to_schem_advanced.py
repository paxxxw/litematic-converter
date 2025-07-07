import sys
import os
import argparse
from pathlib import Path
import traceback
import json
import time
from typing import Dict, List, Optional, Tuple, Any
try:
    from litemapy import Schematic as LitematicSchematic
    from litemapy import Region as LitematicRegion
    from litemapy import BlockState
except ImportError:
    print(
        'Error: litemapy library not found. Install with: pip install litemapy'
        )
    sys.exit(1)
try:
    import nbtlib
except ImportError:
    print('Error: nbtlib library not found. Install with: pip install nbtlib')
    sys.exit(1)

class AdvancedLitematicConverter:

    def __init__(self):
        self.block_palette = {}
        self.block_id_counter = 0
        self.stats = {'total_blocks': 0, 'processed_blocks': 0,
            'unique_blocks': 0, 'entities': 0, 'tile_entities': 0,
            'banners_converted': 0}
        self.color_name_to_id = {'white': 0, 'orange': 1, 'magenta': 2,
            'light_blue': 3, 'yellow': 4, 'lime': 5, 'pink': 6, 'gray': 7,
            'light_gray': 8, 'cyan': 9, 'purple': 10, 'blue': 11, 'brown': 
            12, 'green': 13, 'red': 14, 'black': 15}
        self.pattern_name_mapping = {'minecraft:base': 'b',
            'minecraft:stripe_bottom': 'bs', 'minecraft:stripe_top': 'ts',
            'minecraft:stripe_left': 'ls', 'minecraft:stripe_right': 'rs',
            'minecraft:stripe_center': 'cs', 'minecraft:stripe_middle':
            'ms', 'minecraft:stripe_downright': 'drs',
            'minecraft:stripe_downleft': 'dls', 'minecraft:small_stripes':
            'ss', 'minecraft:cross': 'cr', 'minecraft:straight_cross': 'sc',
            'minecraft:diagonal_left': 'ld', 'minecraft:diagonal_right':
            'rud', 'minecraft:diagonal_up_left': 'lud',
            'minecraft:diagonal_up_right': 'rd', 'minecraft:half_vertical':
            'vh', 'minecraft:half_vertical_right': 'vhr',
            'minecraft:half_horizontal': 'hh',
            'minecraft:half_horizontal_bottom': 'hhb',
            'minecraft:square_bottom_left': 'bl',
            'minecraft:square_bottom_right': 'br',
            'minecraft:square_top_left': 'tl', 'minecraft:square_top_right':
            'tr', 'minecraft:triangle_bottom': 'bt',
            'minecraft:triangle_top': 'tt', 'minecraft:triangles_bottom':
            'bts', 'minecraft:triangles_top': 'tts', 'minecraft:circle':
            'mc', 'minecraft:rhombus': 'mr', 'minecraft:border': 'bo',
            'minecraft:curly_border': 'cbo', 'minecraft:bricks': 'bri',
            'minecraft:gradient': 'gra', 'minecraft:gradient_up': 'gru',
            'minecraft:creeper': 'cre', 'minecraft:skull': 'sku',
            'minecraft:flower': 'flo', 'minecraft:mojang': 'moj',
            'minecraft:globe': 'glb', 'minecraft:piglin': 'pig',
            'minecraft:flow': 'flw', 'minecraft:guster': 'gus'}

    def convert_block_name(self, block_name: str) ->str:
        if ':' in block_name:
            return block_name
        else:
            return f'minecraft:{block_name}'

    def create_block_state_string(self, block: BlockState) ->str:
        block_name = self.convert_block_name(block.id)
        try:
            if hasattr(block, 'properties'):
                props = block.properties
                if callable(props):
                    props = props()
                if props:
                    props_dict = dict(props)
                else:
                    props_dict = {}
                if props_dict:
                    props_sorted = sorted(props_dict.items())
                    prop_str = ','.join([f'{k}={v}' for k, v in props_sorted])
                    return f'{block_name}[{prop_str}]'
                else:
                    return block_name
            else:
                return block_name
        except Exception as e:
            print(f'Debug: Failed to process properties for {block_name}: {e}')
            return block_name

    def get_block_id(self, block_state: str) ->int:
        if block_state not in self.block_palette:
            self.block_palette[block_state] = self.block_id_counter
            self.block_id_counter += 1
        return self.block_palette[block_state]

    def convert_banner_tile_entity(self, litematic_banner) ->Optional[nbtlib
        .Compound]:
        try:
            if hasattr(litematic_banner, 'data') and litematic_banner.data:
                nbt_data = litematic_banner.data
            else:
                print(f'  ⚠️  Banner tile entity missing data')
                return None
            entity_id = nbt_data.get('id', 'minecraft:banner')
            if entity_id != 'minecraft:banner':
                print(f'  ⚠️  Unexpected banner entity ID: {entity_id}')
                return None
            x = nbt_data.get('x', 0)
            y = nbt_data.get('y', 0)
            z = nbt_data.get('z', 0)
            patterns = []
            if 'patterns' in nbt_data:
                litematic_patterns = nbt_data['patterns']
                for pattern_data in litematic_patterns:
                    color = pattern_data.get('color', 'white')
                    pattern = pattern_data.get('pattern', 'minecraft:base')
                    patterns.append(nbtlib.Compound({'color': nbtlib.String
                        (color), 'pattern': nbtlib.String(pattern)}))
            banner_nbt = nbtlib.Compound({'Id': nbtlib.String(
                'minecraft:banner'), 'Pos': nbtlib.IntArray([x, y, z]),
                'Data': nbtlib.Compound({'patterns': nbtlib.List[nbtlib.
                Compound](patterns), 'id': nbtlib.String('minecraft:banner')})}
                )
            self.stats['banners_converted'] += 1
            return banner_nbt
        except Exception as e:
            print(f'  ❌ Error converting banner: {e}')
            traceback.print_exc()
            return None

    def convert_tile_entity(self, litematic_tile_entity) ->Optional[nbtlib.
        Compound]:
        try:
            if hasattr(litematic_tile_entity, 'data'
                ) and litematic_tile_entity.data:
                nbt_data = litematic_tile_entity.data
            else:
                print(f'  ⚠️  Tile entity missing data')
                return None
            entity_id = nbt_data.get('id', 'unknown')
            if entity_id == 'minecraft:banner':
                return self.convert_banner_tile_entity(litematic_tile_entity)
            x = nbt_data.get('x', 0)
            y = nbt_data.get('y', 0)
            z = nbt_data.get('z', 0)
            tile_entity_data = nbtlib.Compound({})
            for key, value in nbt_data.items():
                if key not in ['id', 'x', 'y', 'z']:
                    try:
                        if isinstance(value, str):
                            tile_entity_data[key] = nbtlib.String(value)
                        elif isinstance(value, int):
                            tile_entity_data[key] = nbtlib.Int(value)
                        elif isinstance(value, float):
                            tile_entity_data[key] = nbtlib.Float(value)
                        elif isinstance(value, bool):
                            tile_entity_data[key] = nbtlib.Byte(1 if value else
                                0)
                        elif isinstance(value, list):
                            tile_entity_data[key] = nbtlib.List(value)
                        elif hasattr(value, '__dict__') or isinstance(value,
                            dict):
                            tile_entity_data[key] = nbtlib.Compound(value)
                        else:
                            tile_entity_data[key] = value
                    except Exception as conversion_error:
                        print(
                            f"  ⚠️  Skipping field '{key}' due to conversion error: {conversion_error}"
                            )
                        continue
            wrapped_tile_entity = nbtlib.Compound({'Id': nbtlib.String(
                entity_id), 'Pos': nbtlib.IntArray([x, y, z]), 'Data':
                tile_entity_data})
            self.stats['tile_entities'] += 1
            return wrapped_tile_entity
        except Exception as e:
            print(f'  ❌ Error converting tile entity: {e}')
            traceback.print_exc()
            return None

    def get_tile_entities_from_region(self, region: LitematicRegion) ->List[
        nbtlib.Compound]:
        tile_entities = []
        try:
            if hasattr(region, 'tile_entities'):
                litematic_tile_entities = region.tile_entities
                print(
                    f'Found {len(litematic_tile_entities)} tile entities in region'
                    )
                for i, tile_entity_data in enumerate(litematic_tile_entities):
                    print(
                        f'Processing tile entity {i + 1}/{len(litematic_tile_entities)}'
                        )
                    if hasattr(tile_entity_data, '__dict__'):
                        print(f'  Type: {type(tile_entity_data).__name__}')
                        print(
                            f"  Available attributes: {[attr for attr in dir(tile_entity_data) if not attr.startswith('_')]}"
                            )
                        try:
                            entity_id = getattr(tile_entity_data, 'id',
                                'unknown')
                            print(f'  ID: {entity_id}')
                        except:
                            print(f'  ID: Could not access')
                        try:
                            x = getattr(tile_entity_data, 'x', '?')
                            y = getattr(tile_entity_data, 'y', '?')
                            z = getattr(tile_entity_data, 'z', '?')
                            print(f'  Position: ({x}, {y}, {z})')
                        except:
                            print(f'  Position: Could not access')
                        if hasattr(tile_entity_data, 'patterns'):
                            patterns = getattr(tile_entity_data, 'patterns', []
                                )
                            print(
                                f'  Patterns: {len(patterns) if patterns else 0}'
                                )
                    else:
                        print(f'  Type: Dictionary-like object')
                        print(
                            f"  Keys: {list(tile_entity_data.keys()) if hasattr(tile_entity_data, 'keys') else 'No keys method'}"
                            )
                    converted = self.convert_tile_entity(tile_entity_data)
                    if converted:
                        tile_entities.append(converted)
                        self.stats['tile_entities'] += 1
                        print(f'  ✅ Successfully converted')
                    else:
                        print(f'  ❌ Failed to convert')
            elif hasattr(region, 'tileentities'):
                litematic_tile_entities = region.tileentities
                print(
                    f"Found {len(litematic_tile_entities)} tile entities in region (via 'tileentities')"
                    )
                for tile_entity_data in litematic_tile_entities:
                    converted = self.convert_tile_entity(tile_entity_data)
                    if converted:
                        tile_entities.append(converted)
                        self.stats['tile_entities'] += 1
            else:
                print('Checking for tile entities via other methods...')
                print(
                    f"Region attributes: {[attr for attr in dir(region) if not attr.startswith('_')]}"
                    )
                for attr_name in ['tile_entities', 'tileentities',
                    'block_entities', 'blockentities']:
                    if hasattr(region, attr_name):
                        print(
                            f"Found potential tile entities under '{attr_name}'"
                            )
                        try:
                            entities = getattr(region, attr_name)
                            print(f'  Type: {type(entities)}')
                            print(
                                f"  Length: {len(entities) if hasattr(entities, '__len__') else 'No length'}"
                                )
                        except Exception as e:
                            print(f'  Error accessing {attr_name}: {e}')
                print('No tile entities found via standard methods')
        except Exception as e:
            print(f'Warning: Could not access tile entities from region: {e}')
            print('Continuing without tile entity conversion...')
        return tile_entities

    def create_modern_schematic_nbt(self, width: int, height: int, length: int
        ) ->nbtlib.Compound:
        return nbtlib.Compound({'Version': nbtlib.Int(3), 'DataVersion':
            nbtlib.Int(4325), 'Width': nbtlib.Short(width), 'Height':
            nbtlib.Short(height), 'Length': nbtlib.Short(length), 'Offset':
            nbtlib.IntArray([0, 0, 0]), 'Blocks': nbtlib.Compound({
            'Palette': nbtlib.Compound({}), 'Data': nbtlib.ByteArray([]),
            'BlockEntities': nbtlib.List[nbtlib.Compound]([])}), 'Metadata':
            nbtlib.Compound({'Date': nbtlib.Long(int(time.time() * 1000)),
            'WorldEdit': nbtlib.Compound({'Version': nbtlib.String('7.3.14'
            ), 'EditingPlatform': nbtlib.String('enginehub:fabric'),
            'Origin': nbtlib.IntArray([0, 0, 0]), 'Platforms': nbtlib.
            Compound({'enginehub:fabric': nbtlib.Compound({'Name': nbtlib.
            String('Fabric-Official'), 'Version': nbtlib.String(
            '7.3.14+7149-8bea01b')})})})})})

    def encode_block_data(self, blocks: List[int], palette_size: int) ->bytes:
        if palette_size <= 1:
            bits_per_block = 1
        else:
            bits_per_block = max((palette_size - 1).bit_length(), 1)
        data = bytearray()
        current_long = 0
        bits_used = 0
        for block_id in blocks:
            current_long |= block_id << bits_used
            bits_used += bits_per_block
            while bits_used >= 64:
                for i in range(8):
                    data.append(current_long >> i * 8 & 255)
                current_long >>= 64
                bits_used -= 64
        if bits_used > 0:
            for i in range(8):
                data.append(current_long >> i * 8 & 255)
        return bytes(data)

    def convert_region_to_schematic(self, region: LitematicRegion,
        use_modern_format: bool=True) ->nbtlib.Compound:
        width = region.width
        height = region.height
        length = region.length
        print(f'Converting region: {width}x{height}x{length}')
        print(f'  Original Width: {width}, Height: {height}, Length: {length}')
        if width <= 0 or height <= 0 or length <= 0:
            print(
                f'  ⚠️  Negative/zero dimensions detected, trying alternative methods...'
                )
            width = len(region.xrange())
            height = len(region.yrange())
            length = len(region.zrange())
            print(f'  Using range methods: {width}x{height}x{length}')
            if width <= 0 or height <= 0 or length <= 0:
                width = abs(region.maxx() - region.minx()) + 1
                height = abs(region.maxy() - region.miny()) + 1
                length = abs(region.maxz() - region.minz()) + 1
                print(f'  Using min/max approach: {width}x{height}x{length}')
        print(f'  Final dimensions: {width}x{height}x{length}')
        print(f'  Total volume: {width * height * length}')
        if width <= 0 or height <= 0 or length <= 0:
            print(f'  ❌ Error: Invalid region dimensions after all attempts!')
            print(
                f'  Region min/max: x({region.minx()}, {region.maxx()}), y({region.miny()}, {region.maxy()}), z({region.minz()}, {region.maxz()})'
                )
            return None
        if use_modern_format:
            schematic_nbt = self.create_modern_schematic_nbt(width, height,
                length)
        else:
            schematic_nbt = nbtlib.Compound({'Width': nbtlib.Short(width),
                'Height': nbtlib.Short(height), 'Length': nbtlib.Short(
                length), 'Materials': nbtlib.String('Alpha'), 'Blocks':
                nbtlib.ByteArray([0] * (width * height * length)), 'Data':
                nbtlib.ByteArray([0] * (width * height * length)),
                'Entities': nbtlib.List[nbtlib.Compound]([]),
                'TileEntities': nbtlib.List[nbtlib.Compound]([])})
        self.block_palette = {}
        self.block_id_counter = 0
        blocks = []
        self.stats['total_blocks'] = width * height * length
        self.stats['processed_blocks'] = 0
        print('Converting blocks...')
        print(f'  Region coordinate ranges:')
        print(
            f'    X: {region.minx()} to {region.maxx()} (range: {len(region.xrange())})'
            )
        print(
            f'    Y: {region.miny()} to {region.maxy()} (range: {len(region.yrange())})'
            )
        print(
            f'    Z: {region.minz()} to {region.maxz()} (range: {len(region.zrange())})'
            )
        try:
            test_x = region.minx()
            test_y = region.miny()
            test_z = region.minz()
            test_block = region[test_x, test_y, test_z]
            print(
                f'  Test block at ({test_x}, {test_y}, {test_z}): {test_block} (type: {type(test_block)})'
                )
            print(
                f"  Test block ID: {getattr(test_block, 'id', 'no id attribute')}"
                )
        except Exception as e:
            print(
                f'  Error accessing block at ({test_x}, {test_y}, {test_z}): {e}'
                )
        for rel_y in range(height):
            for rel_z in range(length):
                for rel_x in range(width):
                    try:
                        abs_x = region.minx() + rel_x
                        abs_y = region.miny() + rel_y
                        abs_z = region.minz() + rel_z
                        block = region[abs_x, abs_y, abs_z]
                        if self.stats['processed_blocks'] < 10:
                            print(
                                f"    Block at rel({rel_x}, {rel_y}, {rel_z}) abs({abs_x}, {abs_y}, {abs_z}): {block} (id: {getattr(block, 'id', 'no id')})"
                                )
                        block_state = self.create_block_state_string(block)
                        if 'banner' in block_state.lower():
                            print(
                                f'  Found banner block at ({abs_x}, {abs_y}, {abs_z}): {block_state}'
                                )
                        block_id = self.get_block_id(block_state)
                    except Exception as e:
                        if self.stats['processed_blocks'] < 10:
                            print(
                                f'    Error accessing block at rel({rel_x}, {rel_y}, {rel_z}): {e}'
                                )
                        block_id = self.get_block_id('minecraft:air')
                    blocks.append(block_id)
                    if not use_modern_format:
                        index = (rel_y * length + rel_z) * width + rel_x
                        if block_id <= 255:
                            schematic_nbt['Blocks'][index] = block_id
                        else:
                            schematic_nbt['Blocks'][index] = 0
                        schematic_nbt['Data'][index] = 0
                    self.stats['processed_blocks'] += 1
                    if self.stats['processed_blocks'] % 10000 == 0:
                        progress = 100 * self.stats['processed_blocks'
                            ] / self.stats['total_blocks']
                        print(
                            f"Progress: {self.stats['processed_blocks']}/{self.stats['total_blocks']} blocks ({progress:.1f}%)"
                            )
        air_block_id = self.block_palette.get('minecraft:air', -1)
        non_air_blocks = sum(1 for block_id in blocks if block_id !=
            air_block_id)
        print(f'  Total blocks processed: {len(blocks)}')
        print(f'  Non-air blocks found: {non_air_blocks}')
        print(f'  Air blocks: {len(blocks) - non_air_blocks}')
        print(f'  Blocks in palette: {len(self.block_palette)}')
        if use_modern_format:
            palette = {}
            for block_state, block_id in self.block_palette.items():
                palette[block_state] = nbtlib.Int(block_id)
            temp_banner_blocks = {k: v for k, v in self.block_palette.items
                () if 'banner' in k.lower()}
            if temp_banner_blocks:
                print(f'  Banner blocks in palette: {temp_banner_blocks}')
            schematic_nbt['Blocks']['Palette'] = nbtlib.Compound(palette)
            try:
                block_data = self.encode_block_data(blocks, len(self.
                    block_palette))
                schematic_nbt['Blocks']['Data'] = nbtlib.ByteArray(list(
                    block_data))
            except Exception as e:
                print(
                    f'Warning: Failed to encode block data, using simple encoding: {e}'
                    )
                block_data_bytes = []
                for block_id in blocks:
                    if block_id <= 255:
                        block_data_bytes.append(block_id)
                    else:
                        block_data_bytes.append(0)
                schematic_nbt['Blocks']['Data'] = nbtlib.ByteArray(
                    block_data_bytes)
        self.stats['unique_blocks'] = len(self.block_palette)
        print('Converting tile entities...')
        tile_entities = self.get_tile_entities_from_region(region)
        banner_blocks_in_palette = {k: v for k, v in self.block_palette.
            items() if 'banner' in k.lower()}
        banner_tile_entity_positions = []
        for te in tile_entities:
            if hasattr(te, 'get') and te.get('id') == 'minecraft:banner':
                if hasattr(te, 'get') and 'Pos' in te:
                    pos = te['Pos']
                    if hasattr(pos, '__len__') and len(pos) == 3:
                        banner_tile_entity_positions.append(tuple(pos))
                        print(f'  Banner tile entity at position: {tuple(pos)}'
                            )
        if banner_tile_entity_positions:
            print(
                f'  Total banner tile entities: {len(banner_tile_entity_positions)}'
                )
            print(
                f'  Banner blocks in palette: {len(banner_blocks_in_palette)}')
            if len(banner_tile_entity_positions) != len(
                banner_blocks_in_palette):
                print(
                    f'  ⚠️  Mismatch: {len(banner_tile_entity_positions)} tile entities vs {len(banner_blocks_in_palette)} blocks'
                    )
        if use_modern_format:
            schematic_nbt['Blocks']['BlockEntities'] = nbtlib.List[nbtlib.
                Compound](tile_entities)
        else:
            schematic_nbt['TileEntities'] = nbtlib.List[nbtlib.Compound](
                tile_entities)
        return schematic_nbt

    def convert_litematic_to_schem(self, input_file: str, output_file:
        Optional[str]=None, region_name: Optional[str]=None, all_regions:
        bool=False, use_modern_format: bool=True) ->bool:
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            return False
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f'{base_name}.schem'
        try:
            print(f'Loading litematic file: {input_file}')
            litematic = LitematicSchematic.load(input_file)
            if hasattr(litematic, 'name') and litematic.name:
                print(f'Name: {litematic.name}')
            if hasattr(litematic, 'author') and litematic.author:
                print(f'Author: {litematic.author}')
            if hasattr(litematic, 'description') and litematic.description:
                print(f'Description: {litematic.description}')
            regions = litematic.regions
            region_names = list(regions.keys())
            print(f'Found {len(regions)} region(s): {region_names}')
            if not regions:
                print('Error: No regions found in litematic file.')
                return False
            if all_regions:
                for i, (name, region) in enumerate(regions.items()):
                    region_output = (
                        f'{os.path.splitext(output_file)[0]}_{name}.schem')
                    print(f"\nConverting region '{name}' to {region_output}")
                    schematic_nbt = self.convert_region_to_schematic(region,
                        use_modern_format)
                    root = nbtlib.File({'Schematic': schematic_nbt})
                    root.save(region_output, gzipped=True)
                    print(f"✅ Region '{name}' converted successfully!")
                    self.print_stats()
                return True
            elif region_name:
                if region_name not in regions:
                    print(
                        f"Error: Region '{region_name}' not found. Available: {region_names}"
                        )
                    return False
                region = regions[region_name]
                print(f"Converting region '{region_name}'")
            else:
                if len(regions) > 1:
                    print(
                        f"Warning: Multiple regions found. Converting first region '{region_names[0]}'."
                        )
                    print(
                        'Use --all-regions to convert all, or --region to specify one.'
                        )
                region = list(regions.values())[0]
            schematic_nbt = self.convert_region_to_schematic(region,
                use_modern_format)
            print(f'Saving to: {output_file}')
            root = nbtlib.File({'Schematic': schematic_nbt})
            root.save(output_file, gzipped=True)
            print(f'✅ Conversion completed successfully!')
            print(f'📁 Output: {output_file}')
            self.print_stats()
            return True
        except Exception as e:
            print(f'❌ Error during conversion: {str(e)}')
            print('Full traceback:')
            traceback.print_exc()
            return False

    def print_stats(self):
        print(f'📊 Statistics:')
        print(f"   🧱 Total blocks: {self.stats['processed_blocks']:,}")
        print(f"   🎨 Unique block types: {self.stats['unique_blocks']}")
        if self.stats['entities'] > 0:
            print(f"   👤 Entities: {self.stats['entities']}")
        if self.stats['tile_entities'] > 0:
            print(f"   📦 Tile entities: {self.stats['tile_entities']}")
        if self.stats['banners_converted'] > 0:
            print(f"   🎨 Banners converted: {self.stats['banners_converted']}")

def main():
    parser = argparse.ArgumentParser(description=
        'Advanced Minecraft .litematic to .schem converter',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=
        """
Examples:
  # Convert first region
  python litematic_to_schem_advanced.py castle.litematic
  # Convert specific region
  python litematic_to_schem_advanced.py castle.litematic --region "main"
  # Convert all regions to separate files
  python litematic_to_schem_advanced.py castle.litematic --all-regions
  # Use legacy format (compatible with older tools)
  python litematic_to_schem_advanced.py castle.litematic --legacy
        """
        )
    parser.add_argument('input_file', help='Path to the input .litematic file')
    parser.add_argument('output_file', nargs='?', default=None, help=
        'Path to the output .schem file (optional)')
    parser.add_argument('--region', help='Name of specific region to convert')
    parser.add_argument('--all-regions', action='store_true', help=
        'Convert all regions to separate files')
    parser.add_argument('--legacy', action='store_true', help=
        'Use legacy .schematic format instead of modern .schem')
    parser.add_argument('--version', action='version', version=
        'Advanced Litematic to Schematic Converter 2.0')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    converter = AdvancedLitematicConverter()
    success = converter.convert_litematic_to_schem(input_file=args.
        input_file, output_file=args.output_file, region_name=args.region,
        all_regions=args.all_regions, use_modern_format=not args.legacy)
    if not success:
        sys.exit(1)
if __name__ == '__main__':
    main()