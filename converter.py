from PIL import Image

# Abre a imagem JPG
img = Image.open("Cashflow.jpg")

# Redimensiona e salva no formato de ícone do Windows
# O formato ICO aceita tamanhos como 16x16, 32x32, 64x64, 128x128 ou 256x256
img.save("meu_icone.ico", format="ICO", sizes=[(256, 256)])

print("Ícone gerado com sucesso!")