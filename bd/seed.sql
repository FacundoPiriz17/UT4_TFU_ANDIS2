USE db_games;

-- Usuario de demo:
-- email: demo@adaii.local
-- contraseña: Demo123!
INSERT INTO Persona (
    EmailPersona,
    NombrePersona,
    ApellidoPersona
)
VALUES (
    'demo@adaii.local',
    'Usuario',
    'Demo'
);

INSERT INTO Login (
    EmailPersona,
    ContrasenaLogin
)
VALUES (
    'demo@adaii.local',
    '$2b$12$g95/khE28S0MWLLKyVfDUeBl8ihehINVRTV.kVnSKuH5Zev41nIO2'
);

INSERT INTO Genero (
    NombreGenero,
    DescripcionGenero
)
VALUES
    ('Accion', 'Genero de accion'),
    ('Indie', 'Juegos independientes');

INSERT INTO Juego (
    IdJuego,
    NombreJuego
)
VALUES
    (1, 'Juego Demo Normal'),
    (2, 'Juego Demo Invierno');

INSERT INTO JuegoTieneGenero (
    IdJuego,
    NombreGenero
)
VALUES
    (1, 'Accion'),
    (2, 'Indie');
