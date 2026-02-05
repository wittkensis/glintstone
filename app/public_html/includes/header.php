<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= isset($pageTitle) ? htmlspecialchars($pageTitle) . ' - ' : '' ?>Glintstone</title>
    <link rel="stylesheet" href="/assets/css/kenilworth.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Cuneiform&display=swap" rel="stylesheet">
</head>
<body>
    <header class="site-header">
        <nav class="nav-container">
            <a href="/" class="logo">
                <span class="logo-icon">𒀭</span>
                <span class="logo-text">Glintstone</span>
            </a>
            <ul class="nav-links">
                <li><a href="/tablets/list.php">Tablets</a></li>
                <li><a href="/signs/">Signs</a></li>
                <li><a href="/dictionary/">Dictionary</a></li>
            </ul>
            <div class="nav-search">
                <form action="/tablets/search.php" method="GET">
                    <input type="text" name="q" placeholder="Search...">
                </form>
            </div>
        </nav>
    </header>
