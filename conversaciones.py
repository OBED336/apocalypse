"""Diálogos locales de los compañeros. No necesitan conexión a Internet."""

OPCIONES = ("¿Cómo estás?", "¿Algún consejo para esta zona?", "¿Qué sabes del equipo?", "Hasta luego")

SALUDOS = (
    "¡Sigues en pie! Sabía que volveríamos a encontrarnos. ¿Qué necesitas?",
    "Te vi llegar desde el pasillo. Acércate, tenemos un momento para hablar.",
    "¡Una cara conocida! Ya empezaba a cansarme de hablar con las paredes.",
    "Qué alivio verte. Respira un momento y dime cómo va todo.",
)

ESTADO = (
    "Estoy cansado, pero no pienso rendirme. Mientras sigamos unidos, hay esperanza.",
    "Me duelen las piernas de explorar, pero sigo entero. Tú también cuídate.",
    "He tenido días mejores... y enemigos peores. Todavía me quedan fuerzas.",
    "Estoy bien. Me preocupan los heridos; recuerda usar tus botiquines con Q o punto, según tu jugador.",
)

CONSEJOS = (
    "Despeja las salas para abrir las puertas. Guarda monedas para la tienda entre pisos.",
    "Mira el minimapa: el rojo marca al jefe y el dorado, el tesoro. Explorar tiene recompensa.",
    "No te quedes rodeado. Muévete, usa el golpe y reserva las granadas para los grupos.",
    "Vigila tu salud y tu energía. Cada personaje tiene una habilidad: F para P1 y 0 para P2.",
)

EQUIPO = (
    "Prometimos volver a encontrarnos. Si ves a los demás, diles que sigo luchando.",
    "Nos separamos durante el brote. Sigue buscando en otras salas; quizá encuentres a los demás.",
    "Obed siempre decía que nadie se queda atrás. Esa promesa también cuenta para ti.",
    "Los registros de evacuación pueden darnos pistas. Hay que sobrevivir para reunir al equipo.",
)


SALUDOS += ("Soy Valeria. Creí que estaba sola en esta zona. Me alegra encontrarte. ¿Hablamos?",)
ESTADO += ("Estoy bien. A veces tengo miedo, pero todavía me quedan fuerzas para ayudar al equipo.",)
CONSEJOS += ("Mi habilidad Determinación me protege cinco segundos y recupera mi energía. No olvides guardar una salida.",)
EQUIPO += ("Los he visto luchar por sus amigos. Quiero ayudarles a reunir al equipo y salir de aquí juntos.",)

def respuesta(indice, opcion, nombre_jugador, zona, herido=False):
    """Devuelve una respuesta del personaje al tema elegido por el jugador."""
    if opcion == 0:
        extra = " Te veo herido. Busca un botiquín antes de seguir." if herido else " Me alegra verte, " + nombre_jugador + "."
        return ESTADO[indice] + extra
    if opcion == 1:
        return "En " + zona + " hay que estar alerta. " + CONSEJOS[indice]
    if opcion == 2:
        return EQUIPO[indice]
    raise ValueError("Tema de conversación desconocido")
