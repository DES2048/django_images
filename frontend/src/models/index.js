export class ImageInfo {
    constructor({name, url, marked, mod_date}) {
        this._name = name;
        this._url = url;
        this._marked = marked;
        this._mod_date = mod_date;
    }
    get name() {
        return this._name;
    }
    get url() {
        return this._url;
    }
    get marked() {
        return this._marked;
    }
    get mod_date() {
        return this._mod_date;
    }
}

export class PickerSettings {
    constructor({selected_gallery, show_mode}) {
        this.selected_gallery = selected_gallery;
        this.show_mode = show_mode;
    }
    isEqual(settings) {
        return this.selected_gallery == settings.selected_gallery &&
            this.show_mode == settings.show_mode
    }
}