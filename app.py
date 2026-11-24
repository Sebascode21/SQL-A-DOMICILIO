import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
import certifi

host = "gateway01.eu-central-1.prod.aws.tidbcloud.com"  
puerto = 4000
usuario = "23NaGedD6Xu6yEP.alumno"  
clave = "zSXFpLYX8od3xnGt"
base = "a_domicilio" 

direccion = "mysql+pymysql://" + usuario + ":" + clave + "@" + host + ":" + str(puerto) + "/" + base
motor = create_engine(direccion, connect_args={"ssl": {"ca": certifi.where()}}) 

st.set_page_config(
    page_title="La Consulta",
    layout="wide"
    )

st.title("Los pedidos de la consulta")

st.write("Los datos proceden de una tabla de datos del bar La Consulta")
st.write("Las fechas de dichos datos estan comprendidas entre Septiembre y Noviembre del presente año.")

@st.cache_data
def cargar_datos():
    carta=pd.read_csv("datos/pedidos_limpios.csv")
    plato=pd.read_csv("datos/platos.csv")
    return carta, plato

carta,plato= cargar_datos()

st.write("tenemos",len(carta),"pedidos entregados")
st.write("Tenemos",len(plato),"platos en Carta")

with st.sidebar:
    st.header("Filtros")
    plataforma=sorted(carta["plataforma"].unique())
    plataforma.insert(0,"todas")
    plataforma= st.selectbox("plataforma",plataforma)


    precio_min, precio_max= st.slider("precio del pedido",0,20,(0,20))

    barrio=st.radio("Barrio",["Chamberí", "Malasaña","Lavapiés","Argüelles","Salamanca"])

filtrados=carta

if plataforma != "todas":
    filtrados=filtrados[filtrados["plataforma"]==plataforma]

if barrio != "todas":
    filtrados=filtrados[filtrados["barrio"]==barrio]

filtrados=filtrados[filtrados["total"]>=precio_min]
filtrados=filtrados[filtrados["total"]<=precio_max]

if len(filtrados)==0:
    st.warning("No esta disponible")
    st.stop()

col1,col2,col3=st.columns(3)

with col1:
    st.metric("pedidos", len(carta))

with col2:
    st.metric("Dinero que se queda el bar",f"{filtrados["neto"].sum():,.2f}€")

with col3:
    st.metric("Minutos de media",round(filtrados["minutos"].mean(),2))


tab1,tab2,tab3,tab4=st.tabs(["Tabla","Graficos","Platos mas pedidos","Tu pedido"])

with tab1:
    st.header("La tabla filtrada")
    st.dataframe(filtrados) 

    st.subheader("Busca una entrega")
    texto=st.text_input("Busca por barrio, fecha..")
    if texto !="":
        encontrados= carta[carta["barrio"].str.contains(texto, case=False)]
        st.dataframe(encontrados)

with tab2:
    colx,coly=st.columns(2)

    with colx:
        st.subheader("Pedidos por semana")
        por_semana= carta.groupby("semana")["total"].size()
        st.bar_chart(por_semana, horizontal=True)

    with coly:
        st.subheader("Lo que gana el bar")
        comparar= carta.groupby("plataforma").agg(pedidos=("id", "count"),neto_medio=("neto", "mean"))
        st.bar_chart(comparar, horizontal=True)

with tab3:
    st.subheader("Platos mas pedidos")
    consulta = """
    SELECT c.plato, SUM(l.cantidad) AS total_pedidos
    FROM lineas AS l
    JOIN carta AS c ON l.plato_id=c.id
    WHERE c.categoria NOT LIKE '%%bebida%%'
    GROUP BY c.plato
    ORDER BY total_pedidos DESC
    LIMIT 10;
"""
    pedidos = pd.read_sql(consulta, motor)
    st.bar_chart(pedidos.set_index("plato"),horizontal=True)

with tab4:
    st.subheader("¿Cuanto tardara tu pedido?")
    mi_plataforma=st.selectbox("plataforma", sorted(carta["plataforma"].unique()))
    mi_tipo=st.radio("Barrio",["Chamberí", "Malasaña","Lavapiés","Argüelles","Salamanca"])

    parecidos = carta[carta["plataforma"] == mi_plataforma]  
    parecidos = parecidos[parecidos["barrio"] == mi_tipo]

    if len(parecidos) == 0:
            st.warning("No entregas parecidas a la tuya.")  
            st.stop()

    precio= parecidos["total"].median()
    mediana_precio=carta["total"].median()

    st.metric("pedidos como el tuyo", len(parecidos))
    st.metric("mediana total de los pedidos parecidos",int(precio))
    st.metric("mediana de todos los pedidos",int(mediana_precio))



    if precio >= mediana_precio:  
        st.success("¡Tu pedido está entre los caros!")  
    else:
        st.error("Tu pedido está entre los baratos.") 

    st.subheader("pedidos parecidos al tuyo")
    st.dataframe(parecidos) 