#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Starting automated build and deployment process...\n');

// Step 1: Build React app
console.log('📦 Building React application...');
try {
    execSync('npm run build', { stdio: 'inherit' });
    console.log('✅ React build completed successfully\n');
} catch (error) {
    console.error('❌ React build failed:', error.message);
    process.exit(1);
}

// Step 2: Update Django template with correct static file references
console.log('🔄 Updating Django template with new static file references...');

try {
    // Read the React build index.html
    const reactIndexPath = path.join(__dirname, 'build', 'index.html');
    const reactIndexContent = fs.readFileSync(reactIndexPath, 'utf8');
    
    // Extract JS and CSS file names from the React build
    const jsMatches = reactIndexContent.match(/static\/js\/main\.[a-f0-9]+\.js/g);
    const cssMatches = reactIndexContent.match(/static\/css\/main\.[a-f0-9]+\.css/g);
    
    // Remove 'static/' from the path since Django STATICFILES_DIRS already includes build/static
    const jsFile = jsMatches ? jsMatches[0].replace('static/', '') : 'js/main.js';
    const cssFile = cssMatches ? cssMatches[0].replace('static/', '') : null;
    
    console.log(`📄 Found JS file: ${jsFile}`);
    if (cssFile) {
        console.log(`🎨 Found CSS file: ${cssFile}`);
    }
    
    // Read the Django template
    const djangoTemplatePath = path.join(__dirname, 'templates', 'index.html');
    let djangoTemplate = fs.readFileSync(djangoTemplatePath, 'utf8');
    
    // Replace the preload link for JS files
    djangoTemplate = djangoTemplate.replace(
        /<link[^>]*rel="preload"[^>]*href="[^"]*main\.[a-f0-9]+\.js[^"]*"[^>]*>/g,
        `<link rel="preload" href="/static/${jsFile}?v=${Date.now()}" as="script">`
    );
    
    // Replace the entire script tag for JS files
    djangoTemplate = djangoTemplate.replace(
        /<script[^>]*src="[^"]*main\.[a-f0-9]+\.js[^"]*"[^>]*><\/script>/g,
        `<script src="/static/${jsFile}?v=${Date.now()}"></script>`
    );
    
    // Add or update CSS file reference if it exists
    if (cssFile) {
        // Remove existing CSS link if present
        djangoTemplate = djangoTemplate.replace(
            /<link[^>]*href="[^"]*main\.[a-f0-9]+\.css[^"]*"[^>]*>/g,
            ''
        );
        
        // Add new CSS link in the head section before </head>
        const cssLink = `    <link href="/static/${cssFile}?v=${Date.now()}" rel="stylesheet">`;
        djangoTemplate = djangoTemplate.replace(
            /(.*)<\/head>/s,
            `$1${cssLink}\n</head>`
        );
    }
    
    // Write updated template
    fs.writeFileSync(djangoTemplatePath, djangoTemplate);
    console.log('✅ Django template updated successfully\n');
    
} catch (error) {
    console.error('❌ Failed to update Django template:', error.message);
    process.exit(1);
}

// Step 3: Collect Django static files
console.log('📁 Collecting Django static files...');
try {
    execSync('python manage.py collectstatic --noinput', { stdio: 'inherit' });
    console.log('✅ Django static files collected successfully\n');
} catch (error) {
    console.error('❌ Django collectstatic failed:', error.message);
    console.error('💡 Make sure Django is properly configured and the virtual environment is activated');
    process.exit(1);
}

// Step 4: Display summary
console.log('🎉 Build and deployment completed successfully!');
console.log('');
console.log('📋 Summary:');
console.log('  ✅ React app built and optimized');
console.log('  ✅ Django template updated with new static file references');
console.log('  ✅ Django static files collected and ready to serve');
console.log('');
console.log('🚀 Your application is ready to serve!');
console.log('   Start the server: python manage.py runserver');
console.log('   Access at: http://localhost:8000');
console.log(''); 