const socket = io();
var globaluser = '';
socket.on('posted', function(post) {
    if(currentThreadType == post.type) {
        loadPosts(post.type)
    };
});

const regForm = document.getElementById('reg-form');
regForm.addEventListener('submit', regUser);

async function regUser(event) {
    event.preventDefault();
    const userfield = document.getElementById('reg-username');
    const passfield = document.getElementById('reg-password');
    const passconfield = document.getElementById('reg-confirm-password');

    const result = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: userfield.value,
            password: passfield.value,
            confirmPassword: passconfield.value
        })
    }).then((res) => res.json());

    if(result.status == 'ok') {
        userfield.value = '';
        passfield.value = '';
        passconfield.value = '';
    } else {
        alert(result.message);
    }
};

let loggedin = false;
let currentThreadType = 'Serious';

const loginForm = document.getElementById('login-form');
loginForm.addEventListener('submit', login);

async function login(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username,
            password
        })
    });

    if(response.ok) {
        const result = await response.json();
        console.log('LOGIN', result.username);
        loggedin = true;
        await checkAuth();
        document.getElementById("user-credentials").innerHTML = `<div id="logout">Hello, ${result.username}! <form><input type="submit" value="Logout"></form></div>`;
        globaluser = result.username;
        const logoutForm = document.getElementById('logout');
        logoutForm.addEventListener('submit', logout);    
    } else {
        const error = await response.json();
        alert(error.message);
    }

};

    async function checkAuth() {
        if(loggedin) {
        loggedin = false;
        return; 
        }

        const result = await fetch('/auth').then((res) => res.json());
        console.log('AUTH', result.auth_token);
        localStorage.setItem('auth_token', result);

        if(result.status == 'ok') {
            document.getElementById("user-credentials").innerHTML = `<div id="logout">Hello, ${result.username}! <form><input type="submit" value="Logout"></form></div>`;
            const logoutForm = document.getElementById('logout');
            logoutForm.addEventListener('submit', logout);
        } else {

        }

    }

    async function logout() {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if(result.status == 'ok') {
            document.getElementById("user-credentials").innerHTML = "Logout work"
        } else {
            console.error("Logout Failed", result.message);
        }
    }

function openTab(evt, tabName) {

    // Hiding all elements in the tabcontent class
    var tabContent = document.getElementsByClassName("tabcontent");
    for (var i = 0; i < tabContent.length; i++){
        tabContent[i].style.display = "none";
    }

    // Removing active class from tablinks
    var tabLinks = document.getElementsByClassName("tablink");
    for(var i = 0; i < tabLinks.length; i++){
        tabLinks[i].className = tabLinks[i].className.replace( "active", "");
    }

    // Displaying current tab
    document.getElementById(tabName).style.display = "block";

    // Setting current tab to "active"
    evt.currentTarget.className += " active";

    // Setting current threadType to the selected tab
    currentThreadType = tabName;

    // Load posts for the selected tab
    loadPosts(tabName)

    if (tabName == 'DirectMessage'){
        loadUsers();
    }
}

// Runs when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Opening default tab by automatically clicking it
    document.getElementById("defaulttab").click()
});

async function submitPost(postType){
    var contentID;
    if (postType == 'Serious'){
        contentID = 'serious-post-content';
    } else if (postType == 'NonSerious') {
        contentID = 'non-serious-post-content';
    } else {
        contentID = 'direct-message-post-content';
    }

    // Getting content from the form
    var content = document.getElementById(contentID).value;
    var imageInput = document.getElementById(contentID + '-image');
    // get time from post
    var delay = parseInt(document.getElementById('delay').value);
    console.log(delay)

    // Checking if anything has been typed and if an image has been selected
    if (!content.trim() && !imageInput.files.length){
        alert("Cannot post empty text without image");
        return;
    }

    // Setting up form data
    const formData = new FormData();
    formData.append('text', content);
    formData.append('type', postType);
    formData.append('delay', delay);
    // Check if image is present
    if (imageInput.files[0]) {
        formData.append('image', imageInput.files[0])
    }

    const response = await fetch('/createpost', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    if (response.ok){
        // Clearing textarea
        document.getElementById(contentID).value = '';
        // Clearing image input
        imageInput.value = '';
        // load posts
        loadPosts(postType);

    } else {
        // alert with error message from server or default message
        alert(result.message || "Failed to create post");
    }
}
async function loadPosts(threadType){
    const response = await fetch(`/getposts?threadType=${threadType}`);
    const posts = await response.json();

    var postContainerID;
    if (threadType == 'Serious') {
        postContainerID = 'serious-posts';
    } else if (threadType == 'NonSerious'){
        postContainerID = 'non-serious-posts';
    } else {
        postContainerID = 'direct-message-posts';
    }
    const postContainer = document.getElementById(postContainerID);

    // Clearing existisng posts
    postContainer.innerHTML = "";

    posts.forEach( post => {
        const postElement = document.createElement('div');
        postElement.className = 'post';
        const postDate = new Date(post.timestamp);
        const formattedDate = postDate.toLocaleString(); 
        // Setting post's inner HTML
        let postHTML = `<strong>${post.username}:</strong> ${post.content}<br><small>${formattedDate}</small>`;

        // Checking if image is present
        if (post.imageURL) {
            postHTML += `<img src="${post.imageURL}" alt= "Posted Image" style="max-width:100%; height = auto;">`;
        }
        // Adding the like button
        postHTML += `<div class = "post-likes">
                    <button onclick="likePost('${post.ID}')">Like</button>
                    <span>${post.likeCount} likes</span>
                    </div>`;

        postElement.innerHTML = postHTML;
        /*postElement.innerHTML = `<strong>${post.username}:</strong> ${post.content}
                                <div class = "post-likes">
                                 <button onclick="likePost('${post.ID}')">Like</button>
                                <span>${post.likeCount} likes</span>
                                </div>`;
        */
        postContainer.appendChild(postElement);
    });
}

async function likePost(postID){
    const response = await fetch('/likepost', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({postID: postID})
    });

    const result = await response.json();

    if (response.ok){
        loadPosts(currentThreadType);
    } else {
        alert("Error liking post" + result.message);
    }
}

async function loadUsers(){
    const response = await fetch('/users');
    const users = await response.json();
    const userList = document.getElementById('user-list');
    userList.innerHTML = "";
    users.forEach(user => {
        const userElement = document.createElement('div');
        userElement.innerHTML = user;
        userList.appendChild(userElement);
    });
}

window.onload = checkAuth;