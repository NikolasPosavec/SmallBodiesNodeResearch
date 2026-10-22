#ifndef GEOMETRY_H
#define GEOMETRY_H

#include "definitions.hpp"
#include "mray.hpp"
#include "physicsengine.hpp"
#include "materials.hpp"
#include "smaterial.hpp"
#include <stdexcept>

struct Skip {
    AABB_primitive_id fd;
    Skip(const AABB_primitive_id fd) : fd(fd){}
    bool operator()(const AABB_primitive_id& t) const { 
        return(t == fd);
    }
};


class Geometry{
    public:

        Geometry(std::list<Triangle>& triangles){
               tree = new Tree(triangles.begin(),triangles.end());
               
        }

        ~Geometry(){
            delete tree;
        }

        void trace_in_diffuse(
                            std::vector<SRay>& stack,std::vector<SRay>& stack_diffuse, 
                            PhysicsEngine& physEngine, Detector& detector, Materials& materials){

            
            Ray ray = stack_diffuse.back().extract_ray();
            Ray_intersection intersection;

            //std::cout << stack_diffuse.back().X[0] << "," << stack_diffuse.back().X[1] << "," << stack_diffuse.back().X[2] << std::endl;
            //std::cout << stack_diffuse.back().K[0] << "," << stack_diffuse.back().K[1] << "," << stack_diffuse.back().K[2] << std::endl;

            if(stack_diffuse.back().property == RAYPROPERTY::DIFFUSESCATTERING){
                intersection = tree->first_intersection(ray);
            }else{
                intersection = tree->first_intersection(ray,Skip(stack_diffuse.back().primitive));
            }


            //std::cout << "diffuse" << std::endl;
            //std::cout << stack_diffuse.back().F[0] << ", " << stack_diffuse.back().F[1] << ", " << stack_diffuse.back().F[2] << std::endl;
            //std::cout << stack_diffuse.back().K[0] << ", " << stack_diffuse.back().K[1] << ", " << stack_diffuse.back().K[2] << std::endl;
            //double* AA = stack_diffuse.back().K;
            if(intersection){
                stack_diffuse.back().property = RAYPROPERTY::SCATTERED;
                const Point* p =  std::get_if<Point>(&(intersection->first));
                stack_diffuse.back().primitive = intersection->second;
                Vector3 v = CGAL::normal(intersection->second->vertex(0),
                                         intersection->second->vertex(1), 
                                         intersection->second->vertex(2));

                double N[3] = {v.x(), v.y(), v.z()};
                bool escape = physEngine.escape_diffuse(stack,stack_diffuse,materials.get_first_material((&*intersection->second)),
                                                        materials.get_second_material((&*intersection->second)), p, N, detector);
                if(!escape) physEngine.diffuse_scattering(stack_diffuse, detector);
            }else{
                throw std::runtime_error("Error diffuse scattering should always hit something");
            }   
        }

        void trace_in_nondiffuse(
                            std::vector<SRay>& stack,std::vector<SRay>& stack_diffuse, 
                            PhysicsEngine& physEngine,Detector& detector, Materials& materials){
            Ray ray = stack.back().extract_ray();
            Ray_intersection intersection;
            
            if(stack.back().property == RAYPROPERTY::UNSCATTERED){
                intersection = tree->first_intersection(ray);
            }else{
                intersection = tree->first_intersection(ray,Skip(stack.back().primitive));
            }
            //std::cout << "nondiffuse" << std::endl;
            //std::cout << stack.back().F[0] << ", " << stack.back().F[1] << ", " << stack.back().F[2] << std::endl;
            //std::cout << stack.back().K[0] << ", " << stack.back().K[1] << ", " << stack.back().K[2] << std::endl;
            if (intersection){
                const Point* p =  std::get_if<Point>(&(intersection->first));

                stack.back().primitive = intersection->second;

                Vector3 v = CGAL::normal(intersection->second->vertex(0),
                                         intersection->second->vertex(1), 
                                         intersection->second->vertex(2));
                double N[3] = {v.x(), v.y(), v.z()};
                
                physEngine.handle_nondiffuse_scattering(stack,stack,stack_diffuse,materials.get_first_material((&*intersection->second)),
                                                        materials.get_second_material((&*intersection->second)),p,N,detector);
            }else{
                physEngine.handle_escaping(stack,detector,materials.get_surrounding_material());
            }
        }
    private:
        Tree* tree;
};


#endif