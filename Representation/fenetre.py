# -*- coding: utf-8 -*-
from tkinter import *
from scipy.spatial import ConvexHull
from Utilitaires.pca import pca_matrice
import numpy.linalg
import numpy as np
from Interpretation.importance_composantes import importance

class FenetreAffichage:

    def __init__(self, liste_textes, p, p_ref, noms_auteurs, methode_reduction):
        self.height = 600
        self.width = 600
        self.liste_textes = liste_textes
        self.p = p
        self.p_ref = p_ref

        self.matrice_proportions = None
        self.indices_coefficients_separateurs = []  # Les indices des 10 coordonnées les plus importantes
        self.coefficients_coordonnees = None  # Pondère les coordonnées les plus séparatrices
        self.vecteurs_originaux = []  # Contient les vecteurs des textes avant PCA

        # Création des clusters
        self.noms_auteurs = noms_auteurs
        self.noms_auteurs_inverses = {}
        self.clusters_theoriques_indices = [[] for i in
                                            range(len(noms_auteurs))]  # permettra de calculer l'enveloppe convexe
        self.clusters_concrets_indices = [[] for i in range(len(noms_auteurs))]
        for i in range(len(self.noms_auteurs)):
            self.noms_auteurs_inverses[self.noms_auteurs[i]] = i
        for i in range(len(self.liste_textes)):
            self.clusters_theoriques_indices[self.auteur_theorique(i)].append(i)
            self.clusters_concrets_indices[self.auteur_concret(i)].append(i)

        # Application de methode_reduction
        if methode_reduction == "pca":
            # Application de methode_reduction
            vecteurs = []
            for texte in self.liste_textes:
                vecteurs.append(texte.vecteur)
                self.vecteurs_originaux.append(texte.vecteur)
            vecteurs, self.matrice_proportions = pca_matrice(vecteurs)
            for i in range(len(self.liste_textes)):
                self.liste_textes[i].vecteur = vecteurs[i]

            # Création des variables du système de réévaluation des composantes

            """
            # Méthode basée sur le tri en norme 2 des colonnes de la matrice de PCA
            norme_colonnes = []
            for i in range(len(self.matrice_proportions)):
                norme_colonnes.append(numpy.linalg.norm(self.matrice_proportions[i]))
            self.indices_coefficients_separateurs = sorted(range(1, len(self.matrice_proportions)),
                    key=(lambda k: norme_colonnes[k]))[:min(10, len(self.matrice_proportions))]
            self.coefficients_coordonnees = [1 for i in range(len(self.indices_coefficients_separateurs))]

            self.points = self.normaliser_points(vecteurs)

            """

            # Méthode basée sur la fonction importance_composantes
            clusters_concrets_textes = []
            for cluster_indice in self.clusters_concrets_indices:
                cluster = []
                for indice in cluster_indice:
                    cluster.append(self.liste_textes[i])
                clusters_concrets_textes.append(cluster)
            importance_composantes = importance(clusters_concrets_textes)
            self.indices_coefficients_separateurs = sorted(range(1, len(self.matrice_proportions)),
                                                    key=(lambda k: importance_composantes[k]))[
                                                    :min(10, len(self.matrice_proportions))]
            self.coefficients_coordonnees = [1 for i in range(len(self.indices_coefficients_separateurs))]

            self.points = self.normaliser_points(vecteurs)

        # Création des objets de la fenêtre
        self.theorique = True
        self.affiche_enveloppe = False

        self.objets_dessines = []
        self.fenetre = fenetre = Tk()
        self.canvas = Canvas(fenetre, width=self.width, height=self.height, background="white")
        self.couleurs = ["yellow", "red", "green", "blue", "black", "purple",
                         "brown1", "gray", "cyan", "white", "royal blue", "dark violet"]

        self.theorique_concret_switch = Button(self.fenetre, text="Afficher le résultat du classifieur",
                                               command=self.switch_theorique_concret)
        self.enveloppe_switch = Checkbutton(self.fenetre, text="Afficher les enveloppes convexes",
                                            command=self.switch_points_enveloppe)

        self.scales = []
        for i in range(min(10, len(liste_textes[0].vecteur))):
            sc = Scale(fenetre, orient='vertical', resolution=1, label='X_'+str(i), from_=1, to=100, command=self.change_proportion_builder(i))
            sc.set(1)
            self.scales.append(sc)

    def change_proportion_builder(self, i):
        return lambda arg: self.change_proportion(i, arg)

    def change_proportion(self, i, arg2):
        if arg2 == 0:
            arg = 1
        else:
            arg = arg2
        # on multiplie la matrice de proportion à droite par une matrice de transvection pour multiplier sa i-ème colonne
        transvection = np.identity(len(self.matrice_proportions))
        indice = self.indices_coefficients_separateurs[i]
        transvection[indice][indice] = float(arg)/max(float(self.coefficients_coordonnees[i]), 0.1)
        self.matrice_proportions = np.dot(self.matrice_proportions, transvection)
        self.coefficients_coordonnees[i] = arg

        vecteurs = []
        for k in range(len(self.liste_textes)):
            vecteurs.append(np.dot(self.matrice_proportions, self.liste_textes[k].vecteur))
            # vecteurs.append(np.dot(self.matrice_proportions, self.vecteurs_originaux[k]))
        self.points = self.normaliser_points(vecteurs)
        self.repaint()

    def normaliser_points(self, vecteurs):
        """Transforme un tableau de vecteurs (ayant déjà subi methode_reduction)
        en gardant ses deux premieres dimensions et en les renormalisant pour
        l'affichage dans la fenetre"""
        # On regarde les coordonnees extremales pour les normaliser
        self.xMin = 0
        self.yMin = 0
        self.xMax = 0
        self.yMax = 0
        for vecteur in vecteurs:
            x = vecteur[0]
            y = vecteur[1]
            if x > self.xMax:
                self.xMax = x
            if x < self.xMin:
                self.xMin = x
            if y > self.yMax:
                self.yMax = y
            if y < self.yMin:
                self.yMin = y

        proportion_x = self.width / (self.xMax - self.xMin) * 0.90
        proportion_y = self.height / (self.yMax - self.yMin) * 0.90
        points = []

        for vecteur in vecteurs:
            points.append(
                [(vecteur[0] - self.xMin) * proportion_x + 0.05 * (self.xMax - self.xMin) * proportion_x,
                 (vecteur[1] - self.yMin) * proportion_y + 0.05 * (self.yMax - self.yMin) * proportion_y])
        return points

    def switch_theorique_concret(self):
        self.theorique = not self.theorique
        if self.theorique:
            self.theorique_concret_switch['text'] = "Afficher le résultat du classifieur"
        else:
            self.theorique_concret_switch['text'] = "Afficher la position théorique"
        self.repaint()
    
    def switch_points_enveloppe(self):
        self.affiche_enveloppe = not self.affiche_enveloppe
        self.repaint()

    # Renvoie le numéro de l'auteur théorique
    def auteur_theorique(self, indice):
        return self.noms_auteurs_inverses[self.liste_textes[indice].auteur]

    # A partir de p_ref
    def auteur_concret(self, indice):
        res = 0
        for i in range(0, len(self.p[indice])):
            if self.p[indice][i] > self.p[indice][res]:
                res = i
        return res

    def repaint(self):
        for objet in self.objets_dessines:
            self.canvas.delete(objet)
        self.objets_dessines = []

        for i in range(len(self.liste_textes)):
            if self.theorique:
                indice = self.auteur_theorique(i)
            else:
                indice = self.auteur_concret(i)
            r = 10.
            self.objets_dessines.append(self.canvas.create_oval(
                self.points[i][0] - r / 2, self.points[i][1] - r / 2,
                self.points[i][0] + r / 2, self.points[i][1] + r / 2,
                fill=self.couleurs[indice]))

        if self.affiche_enveloppe:
            if self.theorique:
                clusters = self.clusters_theoriques_indices
            else:
                clusters = self.clusters_concrets_indices
            for k in range(len(clusters)):
                hull = ConvexHull([self.points[i] for i in clusters[k]])
                self.objets_dessines.append(self.canvas.create_polygon(
                    [self.points[clusters[k][i]] for i in hull.vertices],
                    outline=self.couleurs[k], fill="", width=3))

    def build(self):
        self.canvas.grid(row=0, column=0, rowspan=5, columnspan=2)
        self.repaint()

        self.theorique_concret_switch.grid(row=6, column=0)
        self.enveloppe_switch.grid(row=6, column=1)

        frame_auteurs = Frame(self.fenetre, borderwidth=2)
        frame_clusters = Frame(self.fenetre, borderwidth=2)
        for i in range(len(self.noms_auteurs)):
            # Ajout à frame_auteurs
            couleur_canvas = Canvas(frame_auteurs, width=20, height=20, background=self.couleurs[i])
            couleur_canvas.pack(side=LEFT, padx=3, pady=3)
            couleur_label = Label(frame_auteurs, text=self.noms_auteurs[i].title())
            couleur_label.pack(side=LEFT)

            # Ajout à frame_clusters
            cluster_label = Label(frame_clusters, text="Cluster ")
            cluster_label.grid(row=i, column=0, columnspan=2)
            couleur__cluster = Canvas(frame_clusters, width=20, height=20, background=self.couleurs[i])
            couleur__cluster.grid(row=i, column=2)
            cluster_canvas = Canvas(frame_clusters, width=self.width-100, height=20, background="white")

            # nombres_auteurs[n] = nombre de textes de l'auteur n dans le cluster i
            nombres_auteurs = [0] * len(self.noms_auteurs)
            for k in self.clusters_concrets_indices[i]:
                nombres_auteurs[self.auteur_theorique(k)] += 1

            x = 0
            for k in range(len(nombres_auteurs)):
                x2 = x + (self.width-100) * nombres_auteurs[k] / len(self.clusters_concrets_indices[i])
                cluster_canvas.create_rectangle(x, 0, x2, 21, fill=self.couleurs[k])
                x = x2+1
            cluster_canvas.grid(row=i, column=3, columnspan=6)
        frame_auteurs.grid(row=7, column=0, columnspan=2, sticky=W)
        frame_clusters.grid(row=8, column=0, columnspan=2, sticky=W)

        for i in range(len(self.scales)):
            self.scales[i].grid(row=i // 2, column=2+i % 2, sticky=N)

        self.fenetre.mainloop()
