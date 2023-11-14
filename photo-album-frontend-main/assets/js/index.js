document.addEventListener('keydown', (e) => {
    if(e && e.keyCode == 13) {
        search()
    }
});

 async function uploadFile(file, customLabels) {

    var reader = new FileReader();
    var name = file.files[0].name;
    reader.onload = async function () {
        base64 = await reader.result;
        base64 = base64.split(',')[1];
        console.log(base64);
        return sdk.bucketFilenamePut({
                    'filename': name,
                    'bucket': 'upload-photos-b2',
                    'Content-Type': 'text/base64',
                    'x-amz-meta-customLabels': customLabels
                }, base64, {});
    };
    await reader.readAsDataURL(file.files[0]);
    reader.onerror = function (error) {
      console.log('Error: ', error);
    };
}

// /photos
function upload() {
    customLabels = document.getElementById("customLabels").value.split(",")
    photoFile = document.getElementById("photo")

    for (var i = 0; i < customLabels.length; i++) {
        customLabels[i] = customLabels[i].trim();
    }
    
    console.log("custom", customLabels);
    console.log(photoFile)

    if(photoFile != "") {
        uploadFile(photoFile, customLabels)
        .then((response) => {
            console.log(response)
        })
        .catch((error) => {
            console.log(error)
        })
        console.log("File uploaded")

        resetMessage()
        let successDiv = document.getElementById("success")

        if(successDiv) {
            successDiv.style.display = "block"
            successDiv.innerText = "Success"
        }
    } else {
        console.log("File not uploaded")

        resetMessage()
        let errorDiv = document.getElementById("error")

        if(errorDiv) {
            errorDiv.style.display = "block"
            errorDiv.innerText = "Error"
        }
    }

    reset()
}

function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}

// /search
function search() {
    searchKey = document.getElementById("searchKey").value

    if(searchKey) {
        getSearch(searchKey)
        .then((response) => {
            console.log(response)
            let urls = JSON.parse(response.data.body)["search_result"]
            console.log(urls)
            console.log(urls)
            
            let parent = document.getElementById("cardDeck")
            removeAllChildNodes(parent)
            for(let i = 0; i < urls.length; i++) {
                let div = document.createElement('div')
                div.className = "card"
                div.style.width = "18em"
                div.style.display = "inline-block"

                let image = document.createElement('img')
                image.className = "card-img-top"
                image.src = urls[i]
                div.appendChild(image)
                parent.appendChild(div)
            }
            })
            .catch((error) => {
                console.log(error)
            })
    } else {
        console.log("No search key")
    }
}

function reset() {
    document.getElementById("customLabels").value = ""
    document.getElementById("photo").value = ""
}

function resetMessage() {
    let successDiv = document.getElementById("success")
    let errorDiv = document.getElementById("error")

    if(successDiv) {
        successDiv.style.display = "none"
        successDiv.innerText = ""
    }

    if(errorDiv) {
        errorDiv.style.display = "none"
        errorDiv.innerText = ""
    }
}

function cancel() {
    reset()
    resetMessage()
}

function putRequest(binaryBlob, customLabels) {
    return sdk.bucketFilenamePut({
        'x-amz-meta-customLabels': customLabels,
        'bucket': 'upload-photos-b2',
        'filename': 'frontend_flower.png'
    }, 
        binaryBlob
    , {});
}

function getSearch(searchText) {
    // params, body, additionalParams
    return sdk.searchGet({
        'q': searchText
    }, {}, {});
}

click_to_record.addEventListener('click',function(){
    var record = true;
    window.SpeechRecognition = window.webkitSpeechRecognition;

    const recognition = new SpeechRecognition();
    recognition.interimResults = true;

    recognition.addEventListener('result', e => {
        const transcript = Array.from(e.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('')
        document.getElementById("searchKey").value = transcript;
    });
    
    if (record == true) {
        recognition.start();
    }
})