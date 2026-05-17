from machine import ADC, Pin

# EMG 센서 테스트
adc = ADC(Pin(1))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

while True:
    print(f"Sample : {adc.read()}")