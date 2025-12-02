import PySimpleGUI as sg

sg.theme('LightBlue')

layout = [
    [sg.Text('Se esta janela abrir, o PySimpleGUI está funcionando!')],
    [sg.Button('OK')]
]

window = sg.Window('Teste Rápido', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'OK':
        break

window.close()