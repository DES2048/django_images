import {ImageInfo, PickerSettings} from '../models'
import Cookie from 'js-cookie'

const CSRF_COOKIE_NAME = 'csrftoken'
const CSRF_HEADER_NAME = 'X-CSRFToken'

class API {
  constructor() {
    this.endpoints = {
      settings: "/settings/",
      galleries: "/galleries/",
      deleteImage: '/delete-image/',
      images(gallery, show_mode) {
        return `/galleries/${gallery}/images/?show_mode=${show_mode}`;
      },
      deleteImage(gallery, img_name) {
        return `/delete-image/${gallery}/${img_name}`;  
      },
      markImage(gallery, img_name) {
        return `/galleries/${gallery}/images/${img_name}/mark`;
        
      }  
    }
  }
  _getCSRFfromCookie() {
    return Cookie.get(CSRF_COOKIE_NAME);
  }
  _setCSRFToken() {
    return {
      [CSRF_HEADER_NAME] : this._getCSRFfromCookie()
    }
  }
  async getGalleries () {
    const resp = await fetch(this.endpoints.galleries);
    return await resp.json();
  }
  async getSettings () {
    const resp = await fetch(this.endpoints.settings);
    const data =  await resp.json();
    return new PickerSettings(data);
  }
  async saveSettings (settings) {
    return await fetch(this.endpoints.settings, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this._setCSRFToken()
      },
      body: JSON.stringify(settings)
    });
  }
  /**
   * fetch images, filtered by show_mode
   * @param {string} gallery gallery slug
   * @param {string} show_mode one of all, marked or unmarked
   * @returns {Promise<ImageInfo[]>} list of images
   */
  async getImages(gallery, show_mode) {
    const _url = this.endpoints.images(gallery, show_mode);
    const resp = await fetch(_url);
    const data = await resp.json();
    
    return data.map(elem => {
      return new ImageInfo(elem);
      });
    
  }
  async markImage(gallery, img_name) {
    const resp = await fetch(this.endpoints.markImage(gallery, img_name), 
      {
        method: "POST",
        headers: {
          ...this._setCSRFToken()
        }
      }
    );
    return await resp.json();
  }
  async deleteImage(gallery, url) {
    return await fetch(this.endpoints.deleteImage(gallery, url),
      {
        method: "POST",
        headers: {
          ...this._setCSRFToken()
        }
      });
  }
}

export default new API()