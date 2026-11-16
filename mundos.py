    yuri64639-ux
    yrs

Repository navigation

    Code
    Issues
    Pull requests
    Agents
    Actions
    Projects
    Wiki
    Security and quality

    yrs

/
in
main

    Edit
    Preview

Indent mode
Indent size
Line wrap mode
Editing mundos.py file contents
 
520
521
522
523
524
525
526
527
528
529
530
531
532
533
534
535
536
537
538
539
540
541
542
543
544
545
546
547
548
549
550
551
552
553
554
555
556
557
558
559
560
561
562
563
564
565
566
567
568
569
570
571
572
                        div.appendChild(b);
                    }}
                }}
            }} else if (tipoClima === 'estrelas') {{
                estadoClima = (estadoClima + 1) % 2;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 45; i++) {{
                        const e = document.createElement('div');
                        e.className = 'estrela';
                        const tam = (Math.random() * 4 + 2) + 'px';
                        e.style.width = tam; e.style.height = tam;
                        e.style.left = Math.random() * 100 + 'vw';
                        e.style.top = Math.random() * 85 + 'vh';
                        e.style.animationDelay = (Math.random() * 2) + 's';
                        div.appendChild(e);
                    }}
                }}
            }}
        }}

        function criarNaPosicao(emoji, xPct, yPct) {{
            const palco = document.getElementById('palco');
            const el = document.createElement('div');
            el.className = 'bicho'; el.innerText = emoji;
            el.style.left = xPct + 'vw';
            el.style.top = yPct + 'vh';
            let drag = false, ox = 0, oy = 0;
            el.onpointerdown = e => {{
                drag = true; const r = el.getBoundingClientRect();
                ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId);
            }};
            el.onpointermove = e => {{
                if (!drag) return;
                el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 60)) + 'px';
                el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
            }};
            el.onpointerup = e => {{ drag = false; el.releasePointerCapture(e.pointerId); }};
            palco.appendChild(el);
        }}

        function criar(emoji) {{
            criarNaPosicao(emoji, 15 + Math.random() * 65, 50 + Math.random() * 25);
        }}

        function limpar() {{ document.getElementById('palco').innerHTML = ''; }}
        {espalhados_js}
    </script>
    </body>
    </html>
    """

    components.html(html_cenario, height=700, scrolling=False)

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
