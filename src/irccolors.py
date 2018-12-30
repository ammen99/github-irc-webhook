color_codes = {
'white' : '00',
'black' : '01',
'blue'  : '02',
'green' : '03',
'red'   : '04',
'brown' : '05',
'purple': '06',
'orange': '07',
'yellow': '08',
'lime'  : '09',
'teal'  : '10',
'aqua'  : '11',
'royal' : '12',
'pink'  : '13',
'grey'  : '14',
'silver': '15',
}

def color_modifier(color):
    if color == 'reset':
        return '\x0F'

    fmt = ''
    real_color = color
    if color.startswith('bold'):
        fmt += '\x02'
        real_color = color[5:] # remove the "bold-" prefix

    if len(real_color) > 0:
        fmt += '\x03'
        fmt += color_codes[real_color]

    return fmt

def colorize(msg, color):
    return color_modifier(color) + msg + color_modifier('reset')
