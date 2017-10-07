import sc_noughth
import sc_moonwalkco

def process(kp_id):
    list_li = []
    list_li += sc_noughth.process(kp_id)
    list_li += sc_moonwalkco.process(kp_id)
    return list_li 
