      SUBROUTINE ana_initial (ng, tile, model)
!
!! svn $Id: ana_initial.h 878 2017-11-15 04:12:49Z arango $
!!======================================================================
!! Copyright (c) 2002-2017 The ROMS/TOMS Group                         !
!!   Licensed under a MIT/X style license                              !
!!   See License_ROMS.txt                                              !
!=======================================================================
!                                                                      !
!  This subroutine sets initial conditions for momentum and tracer     !
!  type variables using analytical expressions.                        !
!                                                                      !
!=======================================================================
!
      USE mod_param
      USE mod_grid
      USE mod_ncparam
      USE mod_ocean
      USE mod_stepping
!
! Imported variable declarations.
!
      integer, intent(in) :: ng, tile, model

#include "tile.h"
!
      IF (model.eq.iNLM) THEN
        CALL ana_NLMinitial_tile (ng, tile, model,                      &
     &                            LBi, UBi, LBj, UBj,                   &
     &                            IminS, ImaxS, JminS, JmaxS,           &
     &                            GRID(ng) % h,                         &
#ifdef SPHERICAL
     &                            GRID(ng) % lonr,                      &
     &                            GRID(ng) % latr,                      &
#else
     &                            GRID(ng) % xr,                        &
     &                            GRID(ng) % yr,                        &
#endif
#ifdef SOLVE3D
     &                            GRID(ng) % z_r,                       &
     &                            OCEAN(ng) % u,                        &
     &                            OCEAN(ng) % v,                        &
     &                            OCEAN(ng) % t,                        &
#endif
     &                            OCEAN(ng) % ubar,                     &
     &                            OCEAN(ng) % vbar,                     &
     &                            OCEAN(ng) % zeta)
      END IF
!
! Set analytical header file name used.
!
#ifdef DISTRIBUTE
      IF (Lanafile) THEN
#else
      IF (Lanafile.and.(tile.eq.0)) THEN
#endif
        ANANAME(10)=__FILE__
      END IF

      RETURN
      END SUBROUTINE ana_initial
!
!***********************************************************************
      SUBROUTINE ana_NLMinitial_tile (ng, tile, model,                  &
     &                                LBi, UBi, LBj, UBj,               &
     &                                IminS, ImaxS, JminS, JmaxS,       &
     &                                h,                                &
#ifdef SPHERICAL
     &                                lonr, latr,                       &
#else
     &                                xr, yr,                           &
#endif
#ifdef SOLVE3D
     &                                z_r,                              &
     &                                u, v, t,                          &
#endif
     &                                ubar, vbar, zeta)
!***********************************************************************
!
      USE mod_param
      USE mod_parallel
      USE mod_grid
      USE mod_ncparam
      USE mod_iounits
      USE mod_scalars
!
      USE stats_mod, ONLY : stats_2dfld
#ifdef SOLVE3D
      USE stats_mod, ONLY : stats_3dfld
#endif      
!
!  Imported variable declarations.
!
      integer, intent(in) :: ng, tile, model
      integer, intent(in) :: LBi, UBi, LBj, UBj
      integer, intent(in) :: IminS, ImaxS, JminS, JmaxS
!
#ifdef ASSUMED_SHAPE
      real(r8), intent(in) :: h(LBi:,LBj:)
# ifdef SPHERICAL
      real(r8), intent(in) :: lonr(LBi:,LBj:)
      real(r8), intent(in) :: latr(LBi:,LBj:)
# else
      real(r8), intent(in) :: xr(LBi:,LBj:)
      real(r8), intent(in) :: yr(LBi:,LBj:)
# endif
# ifdef SOLVE3D
      real(r8), intent(in) :: z_r(LBi:,LBj:,:)

      real(r8), intent(out) :: u(LBi:,LBj:,:,:)
      real(r8), intent(out) :: v(LBi:,LBj:,:,:)
      real(r8), intent(out) :: t(LBi:,LBj:,:,:,:)
# endif
      real(r8), intent(out) :: ubar(LBi:,LBj:,:)
      real(r8), intent(out) :: vbar(LBi:,LBj:,:)
      real(r8), intent(out) :: zeta(LBi:,LBj:,:)
#else
# ifdef SPHERICAL
      real(r8), intent(in) :: lonr(LBi:UBi,LBj:UBj)
      real(r8), intent(in) :: latr(LBi:UBi,LBj:UBj)
# else
      real(r8), intent(in) :: xr(LBi:UBi,LBj:UBj)
      real(r8), intent(in) :: yr(LBi:UBi,LBj:UBj)
# endif
      real(r8), intent(in) :: h(LBi:UBi,LBj:UBj)
# ifdef SOLVE3D
      real(r8), intent(in) :: z_r(LBi:UBi,LBj:UBj,N(ng))

      real(r8), intent(out) :: u(LBi:UBi,LBj:UBj,N(ng),2)
      real(r8), intent(out) :: v(LBi:UBi,LBj:UBj,N(ng),2)
      real(r8), intent(out) :: t(LBi:UBi,LBj:UBj,N(ng),3,NT(ng))
# endif
      real(r8), intent(out) :: ubar(LBi:UBi,LBj:UBj,3)
      real(r8), intent(out) :: vbar(LBi:UBi,LBj:UBj,3)
      real(r8), intent(out) :: zeta(LBi:UBi,LBj:UBj,3)
#endif
!
!  Local variable declarations.
!
      logical, save :: first = .TRUE.

      integer :: i, itrc, j, k

      TYPE (T_STATS), save :: Stats(7)   ! ubar, vbar, zeta, u, v, t, s

# if defined JMPBUMP
      real(r8) xhere,yhere,hhere,fhere,rhoyHere,rhoxHere,rhoHere
# endif
      
#include "set_bounds.h"
!
!-----------------------------------------------------------------------
!  Initialize field statistics structure.
!-----------------------------------------------------------------------
!
      IF (first) THEN
        first=.FALSE.
        DO i=1,SIZE(Stats,1)
          Stats(i) % count=0.0_r8
          Stats(i) % min=Large
          Stats(i) % max=-Large
          Stats(i) % avg=0.0_r8
          Stats(i) % rms=0.0_r8
        END DO
      END IF
!
!-----------------------------------------------------------------------
!  Initial conditions for 2D momentum (m/s) components.
!-----------------------------------------------------------------------
!
# if defined JMPBUMP
      DO j=JstrT,JendT
         DO i=IstrP,IendT
            xhere=0.5_r8*(xr(i-1,j)+xr(i,j))
            yhere=0.5_r8*(yr(i-1,j)+yr(i,j))
            hhere=0.5_r8*(h(i-1,j)+h(i,j))
            fhere=1.0e-4_r8     !warning, what if Beta-plane run?
            if ((xhere.ge.(JMP_x0-0.5*JMP_xb)).and.                 &
     &             (xhere.le.(JMP_x0+0.5*JMP_xb)).and.                &
     &             (yhere.ge.(JMP_y0-0.5*JMP_yb)).and.                &
     &             (yhere.le.(JMP_y0+0.5*JMP_yb))) then
               rhoyHere= -JMP_rhoAmp*pi/JMP_yb*                                       &
     &              cos(pi/JMP_xb*(xhere-JMP_x0))*                  &
     &              sin(pi/JMP_yb*(yhere-JMP_y0))
               ubar(i,j,1)=g/rho0/fhere*rhoyHere*(hhere)/2.0_r8   !really m/s?
            else
               ubar(i,j,1)=0.0_r8
            endif
         END DO
      END DO
      DO j=JstrP,JendT
         DO i=IstrT,IendT
            xhere=0.5_r8*(xr(i,j-1)+xr(i,j))
            yhere=0.5_r8*(yr(i,j-1)+yr(i,j))
            hhere=0.5_r8*(h(i,j-1)+h(i,j))
            fhere=1.0e-4_r8     !warning, what if Beta-plane run?
            if ((xhere.ge.(JMP_x0-0.5*JMP_xb)).and.                 &
     &             (xhere.le.(JMP_x0+0.5*JMP_xb)).and.                &
     &             (yhere.ge.(JMP_y0-0.5*JMP_yb)).and.                &
     &             (yhere.le.(JMP_y0+0.5*JMP_yb))) then
               rhoxHere= -JMP_rhoAmp*pi/JMP_xb*                                       &
     &              sin(pi/JMP_xb*(xhere-JMP_x0))*                  &
     &              cos(pi/JMP_yb*(yhere-JMP_y0))            
               vbar(i,j,1)=-g/rho0/fhere*rhoxHere*(hhere)/2.0_r8  !really m/s?
            else
               vbar(i,j,1)=0.0_r8
            endif
        END DO
      END DO
# else
      DO j=JstrT,JendT
        DO i=IstrP,IendT
          ubar(i,j,1)=0.0_r8
        END DO
      END DO
      DO j=JstrP,JendT
        DO i=IstrT,IendT
          vbar(i,j,1)=0.0_r8
        END DO
      END DO
# endif
!
!  Report statistics.
!
      CALL stats_2dfld (ng, tile, iNLM, u2dvar, Stats(1),               &
     &                  LBi, UBi, LBj, UBj, ubar(:,:,1))
      IF (DOMAIN(ng)%NorthEast_Corner(tile)) THEN
        WRITE (stdout,10) TRIM(Vname(2,idUbar))//': '//                 &
     &                    TRIM(Vname(1,idUbar)),                        &
     &                     ng, Stats(1)%min, Stats(1)%max
      END IF
      CALL stats_2dfld (ng, tile, iNLM, v2dvar, Stats(2),               &
     &                  LBi, UBi, LBj, UBj, vbar(:,:,1))
      IF (DOMAIN(ng)%NorthEast_Corner(tile)) THEN
        WRITE (stdout,10) TRIM(Vname(2,idVbar))//': '//                 &
     &                    TRIM(Vname(1,idVbar)),                        &
     &                     ng, Stats(2)%min, Stats(2)%max
      END IF
!
!-----------------------------------------------------------------------
!  Initial conditions for free-surface (m).
!-----------------------------------------------------------------------
!
#if defined JMPBUMP
      DO j=JstrT,JendT
         DO i=IstrT,IendT
              if ((xr(i,j).ge.(JMP_x0-0.5*JMP_xb)).and.                 &
     &             (xr(i,j).le.(JMP_x0+0.5*JMP_xb)).and.                &
     &             (yr(i,j).ge.(JMP_y0-0.5*JMP_yb)).and.                &
     &             (yr(i,j).le.(JMP_y0+0.5*JMP_yb))) then
            
                 rhoHere= JMP_rhoAmp*                                       &
     &                cos(pi/JMP_xb*(xr(i,j)-JMP_x0))*                          &
     &                cos(pi/JMP_yb*(yr(i,j)-JMP_y0))
                 zeta(i,j,1)=-h(i,j)/rho0*rhoHere
              else
                 zeta(i,j,1)=0.0_r8
              endif
        END DO
      END DO
#else
      DO j=JstrT,JendT
        DO i=IstrT,IendT
          zeta(i,j,1)=0.0_r8
        END DO
      END DO
#endif
!
!  Report statistics.
!
      CALL stats_2dfld (ng, tile, iNLM, r2dvar, Stats(3),               &
     &                  LBi, UBi, LBj, UBj, zeta(:,:,1))
      IF (DOMAIN(ng)%NorthEast_Corner(tile)) THEN
        WRITE (stdout,10) TRIM(Vname(2,idFsur))//': '//                 &
     &                    TRIM(Vname(1,idFsur)),                        &
     &                     ng, Stats(3)%min, Stats(3)%max
      END IF

#ifdef SOLVE3D
!
!-----------------------------------------------------------------------
!  Initial conditions for 3D momentum components (m/s).
!-----------------------------------------------------------------------
!
#if defined JMPBUMP
      DO k=1,N(ng)
       DO j=JstrT,JendT
          DO i=IstrP,IendT
             xhere=0.5_r8*(xr(i-1,j)+xr(i,j))
             yhere=0.5_r8*(yr(i-1,j)+yr(i,j))
             hhere=0.5_r8*(h(i-1,j)+h(i,j))
             fhere=1.0e-4_r8    !warning, what if Beta-plane run?
             if ((xhere.ge.(JMP_x0-0.5*JMP_xb)).and.                           &
     &            (xhere.le.(JMP_x0+0.5*JMP_xb)).and.                           &
     &            (yhere.ge.(JMP_y0-0.5*JMP_yb)).and.                            &
     &            (yhere.le.(JMP_y0+0.5*JMP_yb))) then
                rhoyHere= -JMP_rhoAmp*pi/JMP_yb*                                       &
     &               cos(pi/JMP_xb*(xhere-JMP_x0))*                              &
     &               sin(pi/JMP_yb*(yhere-JMP_y0))             
                u(i,j,k,1)=g/rho0/fhere*rhoyHere*                                &
     &               (0.5*(z_r(i-1,j,k)+z_r(i,j,k))+hhere)
             else
                u(i,j,k,1)=0.0_r8
            endif
          END DO
        END DO
        DO j=JstrP,JendT
           DO i=IstrT,IendT
            xhere=0.5_r8*(xr(i,j-1)+xr(i,j))
            yhere=0.5_r8*(yr(i,j-1)+yr(i,j))
            hhere=0.5_r8*(h(i,j-1)+h(i,j))
            fhere=1.0e-4_r8     !warning, what if Beta-plane run?
            if ((xhere.ge.(JMP_x0-0.5*JMP_xb)).and.                 &
     &             (xhere.le.(JMP_x0+0.5*JMP_xb)).and.                &
     &             (yhere.ge.(JMP_y0-0.5*JMP_yb)).and.                &
     &             (yhere.le.(JMP_y0+0.5*JMP_yb))) then
               rhoxHere= -JMP_rhoAmp*pi/JMP_xb*                                       &
     &              sin(pi/JMP_xb*(xhere-JMP_x0))*                  &
     &              cos(pi/JMP_yb*(yhere-JMP_y0))               
               v(i,j,k,1)=-g/rho0/fhere*rhoxHere*                                &
     &               (0.5*(z_r(i,j-1,k)+z_r(i,j,k))+hhere)
            else
               v(i,j,k,1)=0.0_r8
            endif
          END DO
        END DO
      END DO
#else
      DO k=1,N(ng)
       DO j=JstrT,JendT
         DO i=IstrP,IendT
            u(i,j,k,1)=0.0_r8
          END DO
        END DO
        DO j=JstrP,JendT
          DO i=IstrT,IendT
            v(i,j,k,1)=0.0_r8
          END DO
        END DO
      END DO
#endif
!
!  Report statistics.
!
      CALL stats_3dfld (ng, tile, iNLM, u3dvar, Stats(4),               &
     &                  LBi, UBi, LBj, UBj, 1, N(ng), u(:,:,:,1))
      IF (DOMAIN(ng)%NorthEast_Corner(tile)) THEN
        WRITE (stdout,10) TRIM(Vname(2,idUvel))//': '//                 &
     &                    TRIM(Vname(1,idUvel)),                        &
     &                    ng, Stats(4)%min, Stats(4)%max
      END IF
      CALL stats_3dfld (ng, tile, iNLM, v3dvar, Stats(5),               &
     &                  LBi, UBi, LBj, UBj, 1, N(ng), v(:,:,:,1))
      IF (DOMAIN(ng)%NorthEast_Corner(tile)) THEN
        WRITE (stdout,10) TRIM(Vname(2,idVvel))//': '//                 &
     &                    TRIM(Vname(1,idVvel)),                        &
     &                    ng, Stats(5)%min, Stats(5)%max
      END IF
!
!-----------------------------------------------------------------------
!  Initial conditions for tracer type variables.
!-----------------------------------------------------------------------
!
!  Set initial conditions for potential temperature (Celsius) and
!  salinity (PSU).
!
# if defined UPWELLING
      DO k=1,N(ng)
        DO j=JstrT,JendT
          DO i=IstrT,IendT
            t(i,j,k,1,itemp)=T0(ng)+8.0_r8*EXP(z_r(i,j,k)/50.0_r8)
!!          t(i,j,k,1,itemp)=T0(ng)+(z_r(i,j,k)+75.0_r8)/150.0_r8+
!!   &                       4.0_r8*(1.0_r8+TANH((z_r(i,j,k)+35.0_r8)/
!!   &                                           6.5_r8))
!!          t(i,j,k,1,isalt)=1.0E-04_r8*yr(i,j)-S0(ng)
            t(i,j,k,1,isalt)=S0(ng)
!!          IF (j.lt.Mm(ng)/2) THEN
!!            t(i,j,k,1,isalt)=0.0_r8
!!          ELSE IF (j.eq.Mm(ng)/2) THEN
!!            t(i,j,k,1,isalt)=0.5_r8
!!          ELSE IF (j.gt.Mm(ng)/2) THEN
!!            t(i,j,k,1,isalt)=1.0_r8
!!          END IF
          END DO
        END DO
      END DO
# elif defined JMPBUMP
      DO k=1,N(ng)
        DO j=JstrT,JendT
           DO i=IstrT,IendT
              if ((xr(i,j).ge.(JMP_x0-0.5*JMP_xb)).and.                 &
     &             (xr(i,j).le.(JMP_x0+0.5*JMP_xb)).and.                &
     &             (yr(i,j).ge.(JMP_y0-0.5*JMP_yb)).and.                &
     &             (yr(i,j).le.(JMP_y0+0.5*JMP_yb))) then
                 t(i,j,k,1,itemp)=T0(ng)-(JMP_rhoAmp/R0(ng)/Tcoef(ng))* &
     &                cos(pi/JMP_xb*(xr(i,j)-JMP_x0))*           &
     &                cos(pi/JMP_yb*(yr(i,j)-JMP_y0))-                  &
     &                (JMP_rhoStrat/R0(ng)/Tcoef(ng))*z_r(i,j,k)
                 t(i,j,k,1,isalt)=S0(ng)
              else
                 t(i,j,k,1,itemp)=T0(ng)-                               &
     &                (JMP_rhoStrat/R0(ng)/Tcoef(ng))*z_r(i,j,k)
                 t(i,j,k,1,isalt)=S0(ng)
              endif
          END DO
        END DO
      END DO
# else
      DO k=1,N(ng)
        DO j=JstrT,JendT
          DO i=IstrT,IendT
            t(i,j,k,1,itemp)=T0(ng)
#  ifdef SALINITY
            t(i,j,k,1,isalt)=S0(ng)
#  endif
          END DO
        END DO
      END DO
# endif
!
!  Report statistics.
!
      DO itrc=1,NAT
        CALL stats_3dfld (ng, tile, iNLM, u3dvar, Stats(itrc+5),        &
     &                    LBi, UBi, LBj, UBj, 1, N(ng), t(:,:,:,1,itrc))
        IF (DOMAIN(ng)%NorthEast_Corner(tile)) THEN
          WRITE (stdout,10) TRIM(Vname(2,idTvar(itrc)))//': '//         &
     &                      TRIM(Vname(1,idTvar(itrc))),                &
     &                      ng, Stats(itrc+5)%min, Stats(itrc+5)%max
        END IF
      END DO
#endif
!
  10  FORMAT (3x,' ANA_INITIAL - ',a,/,19x,                             &
     &        '(Grid = ',i2.2,', Min = ',1p,e15.8,0p,                   &
     &                         ' Max = ',1p,e15.8,0p,')')

      RETURN
      END SUBROUTINE ana_NLMinitial_tile
