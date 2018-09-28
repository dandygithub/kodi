#import sc_noughth
import sc_moonwalkco
import sc_hdgo
import sc_kodik
#import sc_videoframe
# import sc_getmovie
import sc_hdnow

def process(kp_id):
    list_li = []
#    list_li += sc_noughth.process(kp_id)
    list_li += sc_moonwalkco.process(kp_id)
    list_li += sc_hdgo.process(kp_id)
    list_li += sc_kodik.process(kp_id)
#    list_li += sc_videoframe.process(kp_id)
#    list_li += sc_getmovie.process(kp_id)
#    list_li += sc_hdnow.process(kp_id)
    return list_li 
