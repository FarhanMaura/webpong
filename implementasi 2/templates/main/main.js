// Initialize Application
$(document).ready(function() {
    console.log('🚀 Sistem Deteksi Ujaran Kebencian Initialized');
    initializeApp();
    setupEventListeners();
    console.log('✅ System initialized successfully');
});

function initializeApp() {
    // Update user interface
    updateUserInterface();

    // Add floating animation to elements
    $('.logo').addClass('floating');
    $('.sidebar-logo').addClass('floating');
}

function setupEventListeners() {
    // Sidebar toggle
    $('#toggleSidebar').on('click', toggleSidebar);

    // Mobile menu
    $('#mobileMenuBtn').on('click', toggleMobileMenu);

    // Close mobile menu when clicking on a link
    $('.nav-link').on('click', function() {
        if ($(window).width() <= 768) {
            $('#sidebar').removeClass('show');
        }
    });

    // Auto-resize textareas
    $('textarea').on('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle window resize
    $(window).on('resize', function() {
        if ($(window).width() > 768) {
            $('#sidebar').removeClass('show');
        }
    });
}

function toggleSidebar() {
    const sidebar = $('#sidebar');
    const mainContent = $('#mainContent');
    const toggleIcon = $('#toggleSidebar i');

    sidebar.toggleClass('collapsed');
    mainContent.toggleClass('expanded');

    if (sidebar.hasClass('collapsed')) {
        toggleIcon.removeClass('fa-chevron-left').addClass('fa-chevron-right');
    } else {
        toggleIcon.removeClass('fa-chevron-right').addClass('fa-chevron-left');
    }
}

function toggleMobileMenu() {
    $('#sidebar').toggleClass('show');
}

function updateUserInterface() {
    // Update user info if available
    const userName = "{{ session.get('name', 'User') }}";
    const userEmail = "{{ session.get('email', '') }}";

    if (userName && userName !== 'None') {
        $('.user-name').text(userName);
    }
    if (userEmail && userEmail !== 'None') {
        $('.user-email').text(userEmail);
    }
}

function showTemporaryAlert(icon, title, text) {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });

    Toast.fire({
        icon: icon,
        title: title,
        text: text
    });
}

// Global function to show loading
function showLoading() {
    $('#loadingOverlay').show();
}

// Global function to hide loading
function hideLoading() {
    $('#loadingOverlay').hide();
}