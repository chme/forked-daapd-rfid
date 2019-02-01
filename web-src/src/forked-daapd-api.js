
import axios from 'axios'
import store from '@/store'


export default {

  is_track (uri) {
    return uri && uri.startsWith('library:track:')
  },

  is_album (uri) {
    return uri && uri.startsWith('library:album:')
  },

  is_artist (uri) {
    return uri && uri.startsWith('library:artist:')
  },

  is_playlist (uri) {
    return uri && uri.startsWith('library:playlist:')
  },

  get_id_from_uri (uri) {
    if (!uri) {
      return false
    }
    var i = uri.lastIndexOf(':')
    if (i < 0) {
      return false
    }
    return uri.substring(i + 1)
  },

  load_track (id) {
    return axios.get(store.state.forked_daapd_url + '/api/library/tracks/' + id)
  },

  load_album (id) {
    return axios.get(store.state.forked_daapd_url + '/api/library/albums/' + id)
  },

  load_artist (id) {
    return axios.get(store.state.forked_daapd_url + '/api/library/artists/' + id)
  },

  load_playlist (id) {
    return axios.get(store.state.forked_daapd_url + '/api/library/playlists/' + id)
  },

  load_albums () {
    return axios.get(store.state.forked_daapd_url + '/api/library/albums')
  }
}
