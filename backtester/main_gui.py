
#    sma.name = f"SMA_{length}"

import PySimpleGUI as sg
from indicators import *
from nsetools import Nse
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
from datetime import date
matplotlib.use('TkAgg')

nse=Nse()

# Set theme
#sg.theme('dark grey 9')

# list of intervals - '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'

def elements():
    # Data input pane
    inp_column = [
        [
            sg.Text("Stock name: ", background_color='white', text_color='black'),
            sg.In(size=(25, 1), enable_events=True, key="stock")
        ],
        [
            sg.Text("From: ", background_color='white', text_color='black'),
            sg.In(size=(10,1), key="start", enable_events=True),
            sg.CalendarButton("yyyy-mm-dd", target="start", format='%Y-%m-%d', location=(15,15))
        ],
        [
            sg.Text("To: ", background_color='white', text_color='black'),
            sg.In(size=(10,1), key="end", enable_events=True),
            sg.CalendarButton("yyyy-mm-dd", target="end", format='%Y-%m-%d', location=(15,15))
        ],
        [
            sg.Text("Interval: ", background_color='white', text_color='black'),
            sg.Spin(values=['3mo', '1mo', '1wk', '5d', '1d', '90m', '60m', '30m', '15m', '5m', '2m', '1m'], key="interval", size=(8,1), initial_value='1d')
        ],
        [
            sg.Text("SMA: ", background_color='white', text_color='black'),
            sg.Spin(values=[i for i in range (1,100)], key='sma1', size=(8,1), initial_value=9),
            sg.Text("SMA: ", background_color='white', text_color='black'),
            sg.Spin(values=[i for i in range (1,100)], key='sma2', size=(8,1), initial_value=20)
        ],
        [
            sg.Button("Proceed"),
            sg.Button("Reset")
        ],
        [
            sg.HorizontalSeparator()
        ],
        [
            sg.Text("Live Data", background_color='white', text_color='black')
        ],
        [
            sg.Text("Interval: ", background_color='white', text_color='black'),
            sg.Spin(values=['90m', '60m', '30m', '15m', '5m', '2m', '1m'], key="live_interval", size=(8,1), initial_value='15m'),
            sg.Button("Show Live Data", key='live')
        ],
        [
            sg.Button("Exit")
        ],
        [
            sg.Text("\nTotal profit: ", background_color='white', text_color='black'),
            sg.Text("", size=(10,2), background_color='white', text_color='black', key='net_value'),
        ]
    ]

    # Graph Output Pane
    graph_column = [
        [
            #sg.Text("Chart: ", background_color='white', text_color='black'),
            sg.Canvas(key="canvas", background_color='grey')
        ]
    ]

    # Menu Definition
    menu_def=['&File', ['&New File', '&Open...','Open &Module','---', '!&Recent Files','A&bout','Properties','C&lose']],['&Save',['&Save File', 'Save &As','Save &Copy'  ]],['&Edit', ['&Cut', '&Copy', '&Paste']]

    # ----- Full layout -----
    layout = [
        [
            sg.Menu(menu_def, pad=(10,10))
        ],
        [
            sg.Column(inp_column, background_color='white', vertical_alignment='Top'),
            sg.VSeperator(),
            sg.Column(graph_column, background_color='white'),
        ]
    ]
    return layout

def second_window():

    layout = [[sg.Text('The second form is small \nHere to show that opening a window using a window works')],
              [sg.OK()]]

    window = sg.Window('Second Form', layout)
    event, values = window.read()
    window.close()

def display():
    layout=elements()
    window = sg.Window("Backtester", layout, size=(1200,610), background_color='white', finalize=True, resizable=True)

    stock = window['stock']
    start = window['start']
    end = window['end']
    canvas = window['canvas']
    net_val = window['net_value']
    today = date.today().strftime(format="%Y-%m-%d")

    # To get the canvas figure
    def draw_figure(canvas, figure):
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    def delete_figure_agg(fig_canvas_agg):
        fig_canvas_agg.get_tk_widget().forget()
        #plt.close('all')

    fig_canvas_agg = None

    # Run the Event Loop
    while True:
        event, values = window.read()
        print(values)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        # Reset the data
        if event == "Reset":
            try:
                stock.update('')
                start.update('')
                end.update('')
                delete_figure_agg(fig_canvas_agg)
            except:
                break

        # Stock name was filled in, get data for the stock
        if event == "Proceed":
            if nse.is_valid_code(values['stock']):
                if values['start']<values['end'] and values['start']<today:
                    if fig_canvas_agg:
                        delete_figure_agg(fig_canvas_agg)
                    data = plot(values['stock'], start=values['start'], end=values['end'], interval=values['interval'], s1=values['sma1'], s2=values['sma2'])
                    fig_canvas_agg = draw_figure(canvas.TKCanvas, data)

                    value = net(values['stock'], start=values['start'], end=values['end'], interval=values['interval'], s1=values['sma1'], s2=values['sma2'])
                    net_val.update("\n"+str(value))
                else:
                    sg.popup("""\nEnter valid date\n""", grab_anywhere=True)
            else:
                sg.popup("""\nEnter valid stock code\n""", grab_anywhere=True)
            stock.update('')
            start.update('')
            end.update('')
        elif event == "live":
            if nse.is_valid_code(values['stock']):
                if fig_canvas_agg:
                    delete_figure_agg(fig_canvas_agg)
                plot_live(values['stock'], interval=values['live_interval'], s1=values['sma1'], s2=values['sma2'])
            else:
                sg.popup("""\nEnter valid stock code\n""", grab_anywhere=True)
            stock.update('')
            start.update('')
            end.update('')

        if event == 'About':
#            window.disappear()
            sg.popup('About this program', 'Version 1.0', 'PySimpleGUI Version', sg.version,  grab_anywhere=True)
#            window.reappear()
        elif event == 'Properties':
            second_window()

    window.close()

display()
