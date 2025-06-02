
import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    ventas = pd.read_excel("Base_Margenes_v3.xlsx", sheet_name="LIBRO DE VENTAS")
    recetas = pd.read_excel("Base_Margenes_v3.xlsx", sheet_name="RECETAS DE PRODUCTOS")
    insumos_hist = pd.read_excel("Base_Margenes_v3.xlsx", sheet_name="PRECIO DE INSUMOS")
    return ventas, recetas, insumos_hist

ventas, recetas, insumos_hist = load_data()

ventas["MES"] = pd.to_datetime(ventas["FECHA"]).dt.to_period("M").astype(str)
insumos_hist["MES"] = insumos_hist["FECHA"].astype(str)

st.title("Consulta de Márgenes por Cliente y Producto")

clientes = sorted(ventas["CLIENTE"].unique())
ventas["PRODUCTO COMPLETO"] = ventas["CODIGO PRODUCTO"] + " - " + ventas["NOMBRE DE PRODUCTO"]
productos = sorted(ventas["PRODUCTO COMPLETO"].unique())
meses = sorted(ventas["MES"].unique())

mes_sel = st.selectbox("Selecciona el mes", ["Todos"] + meses)
cli_sel = st.selectbox("Selecciona el cliente", ["Todos"] + clientes)
prod_sel = st.selectbox("Selecciona el producto", ["Todos"] + productos)

if prod_sel != "Todos":
    prod_sel_codigo = prod_sel.split(" - ")[0]
else:
    prod_sel_codigo = "Todos"

df = ventas.copy()
if mes_sel != "Todos":
    df = df[df["MES"] == mes_sel]
if cli_sel != "Todos":
    df = df[df["CLIENTE"] == cli_sel]
if prod_sel_codigo != "Todos":
    df = df[df["CODIGO PRODUCTO"] == prod_sel_codigo]

# Expandir recetas por mes y unir con histórico de precios
meses_validos = df["MES"].unique()
recetas_exp = pd.DataFrame()
for mes in meses_validos:
    temp = recetas.copy()
    temp["MES"] = mes
    recetas_exp = pd.concat([recetas_exp, temp])

# Obtener último precio disponible hacia atrás
insumos_hist_sorted = insumos_hist.sort_values(["CODIGO INSUMO", "MES"])
insumos_hist_filled = insumos_hist_sorted.groupby("CODIGO INSUMO").ffill()
recetas_exp = recetas_exp.merge(insumos_hist_filled, on=["CODIGO INSUMO", "MES"], how="left")
recetas_exp["PRECIO"] = recetas_exp["PRECIO"].fillna(0)
recetas_exp["COSTO_UNITARIO"] = recetas_exp["CANTIDAD"] * recetas_exp["PRECIO"]

costos_mensuales = recetas_exp.groupby(["CODIGO PRODUCTO", "MES"])["COSTO_UNITARIO"].sum().reset_index()

df = df.merge(costos_mensuales, on=["CODIGO PRODUCTO", "MES"], how="left")
df["COSTO_UNITARIO"] = df["COSTO_UNITARIO"].fillna(0)
df["INGRESO TOTAL"] = df["CANTIDAD"] * df["PRECIO UNITARIO"]
df["COSTO TOTAL"] = df["CANTIDAD"] * df["COSTO_UNITARIO"]
df["MARGEN $"] = df["INGRESO TOTAL"] - df["COSTO TOTAL"]
df["MARGEN %"] = df["MARGEN $"] / df["INGRESO TOTAL"]
df["MARGEN %"] = df["MARGEN %"].fillna(0)

# KPIs
st.subheader("Indicadores")
col1, col2, col3 = st.columns(3)
col1.metric("Ventas Netas", f"$ {df['INGRESO TOTAL'].sum():,.0f}")
col2.metric("Costo Total", f"$ {df['COSTO TOTAL'].sum():,.0f}")
col3.metric("Margen Promedio", f"{(df['MARGEN %'].mean()*100):.1f} %")

# Mostrar tabla
st.subheader("Detalle por Factura")
st.dataframe(df[[
    "NÚMERO", "FECHA", "CLIENTE", "NOMBRE DE PRODUCTO", "MES", "CANTIDAD",
    "PRECIO UNITARIO", "INGRESO TOTAL", "COSTO TOTAL", "MARGEN $", "MARGEN %"
]])
