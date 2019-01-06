import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    conf: {
      'daapd_host': '',
      'daapd_port': 0
    },
    current_tag: {
      'id': 0,
      'content': ''
    }
  },

  getters: {
  },

  mutations: {
    setConf (state, conf) {
      state.conf = conf
    },
    setCurrentTag (state, tag) {
      state.current_tag = tag
    }
  },

  actions: {
  }
})
